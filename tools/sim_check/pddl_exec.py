#!/usr/bin/env python3
"""Minimal PDDL parser, grounder and state-transition executor.

Supports the fragment used by the Boulder Dash domains in this repo:
typing, negative / disjunctive / universal / existential preconditions,
conditional effects, universal effects and (ignored) action costs.

Grounding prunes with static predicates (those never changed by any effect),
similar in spirit to Fast Downward's translator, so the ground action counts it
reports are a useful proxy for planner-side model size.
"""

from __future__ import annotations

import itertools
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

# --------------------------------------------------------------------------
# S-expressions
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\(|\)|[^\s()]+")


def parse_sexp(text: str):
    text = re.sub(r";[^\n]*", "", text).lower()
    tokens = _TOKEN_RE.findall(text)
    stack: List[list] = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok)
    if len(stack) != 1:
        raise ValueError("Unbalanced parentheses")
    return stack[0][0]


def _typed_list(items: Sequence[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    pending: List[str] = []
    i = 0
    while i < len(items):
        tok = items[i]
        if tok == "-":
            typ = items[i + 1]
            out.extend((name, typ) for name in pending)
            pending = []
            i += 2
            continue
        pending.append(tok)
        i += 1
    out.extend((name, "object") for name in pending)
    return out


# --------------------------------------------------------------------------
# Domain / problem
# --------------------------------------------------------------------------


@dataclass
class Action:
    name: str
    params: List[Tuple[str, str]]
    pre: object
    eff: object


@dataclass
class Domain:
    name: str
    supertypes: Dict[str, Set[str]]
    actions: List[Action]
    predicates: Set[str]


@dataclass
class Problem:
    name: str
    objects: Dict[str, str]
    init: Set[Tuple[str, ...]]
    goal: object


def parse_domain(text: str) -> Domain:
    sexp = parse_sexp(text)
    name = ""
    parents: Dict[str, Set[str]] = {}
    actions: List[Action] = []
    predicates: Set[str] = set()
    for sec in sexp[1:]:
        head = sec[0]
        if head == "domain":
            name = sec[1]
        elif head == ":types":
            for child, parent in _typed_list(sec[1:]):
                if child != parent:
                    parents.setdefault(child, set()).add(parent)
        elif head == ":predicates":
            for p in sec[1:]:
                predicates.add(p[0])
        elif head == ":action":
            aname = sec[1]
            fields = {sec[i]: sec[i + 1] for i in range(2, len(sec) - 1, 2)}
            params = _typed_list(fields.get(":parameters", []))
            actions.append(Action(aname, params, fields.get(":precondition", ["and"]), fields.get(":effect", ["and"])))
        elif head == ":derived":
            raise NotImplementedError("derived predicates are not supported")
    # transitive closure of supertypes
    sup: Dict[str, Set[str]] = {}

    def ancestors(t: str, seen: Set[str]) -> Set[str]:
        res = {t, "object"}
        for p in parents.get(t, ()):
            if p not in seen:
                res |= ancestors(p, seen | {p})
        return res

    for t in set(parents) | {p for ps in parents.values() for p in ps}:
        sup[t] = ancestors(t, {t})
    return Domain(name, sup, actions, predicates)


def parse_problem(text: str) -> Problem:
    sexp = parse_sexp(text)
    name = ""
    objects: Dict[str, str] = {}
    init: Set[Tuple[str, ...]] = set()
    goal: object = ["and"]
    for sec in sexp[1:]:
        head = sec[0]
        if head == "problem":
            name = sec[1]
        elif head == ":objects":
            for obj, typ in _typed_list(sec[1:]):
                objects[obj] = typ
        elif head == ":init":
            for atom in sec[1:]:
                if atom[0] in ("=", "not"):
                    continue
                init.add(tuple(atom))
        elif head == ":goal":
            goal = sec[1]
    return Problem(name, objects, init, goal)


# --------------------------------------------------------------------------
# Grounding
# --------------------------------------------------------------------------

TRUE = ("true",)
FALSE = ("false",)


def _collect_effect_preds(eff, out: Set[str]) -> None:
    if not isinstance(eff, list) or not eff:
        return
    head = eff[0]
    if head == "and":
        for e in eff[1:]:
            _collect_effect_preds(e, out)
    elif head == "not":
        _collect_effect_preds(eff[1], out)
    elif head == "when":
        _collect_effect_preds(eff[2], out)
    elif head == "forall":
        _collect_effect_preds(eff[2], out)
    elif head in ("increase", "decrease", "assign"):
        return
    else:
        out.add(head)


def _free_vars(f) -> Set[str]:
    if not isinstance(f, list):
        return {f} if isinstance(f, str) and f.startswith("?") else set()
    if f and f[0] in ("forall", "exists"):
        bound = {v for v, _ in _typed_list(f[1])}
        return _free_vars(f[2]) - bound
    out: Set[str] = set()
    for sub in f[1:] if f and isinstance(f[0], str) else f:
        out |= _free_vars(sub)
    return out


def _subst(arg: str, binding: Dict[str, str]) -> str:
    return binding.get(arg, arg) if arg.startswith("?") else arg


class Task:
    """Grounded task. Fluent atoms are mapped to integer ids."""

    def __init__(self, domain: Domain, problem: Problem):
        self.domain = domain
        self.problem = problem
        fluent_preds: Set[str] = set()
        for act in domain.actions:
            _collect_effect_preds(act.eff, fluent_preds)
        self.fluent_preds = fluent_preds
        self.static = {a for a in problem.init if a[0] not in fluent_preds}
        self.static_index: Dict[Tuple[str, int, str], Set[Tuple[str, ...]]] = {}
        for atom in self.static:
            for i, arg in enumerate(atom[1:]):
                self.static_index.setdefault((atom[0], i, arg), set()).add(atom)
        self.static_by_pred: Dict[str, Set[Tuple[str, ...]]] = {}
        for atom in self.static:
            self.static_by_pred.setdefault(atom[0], set()).add(atom)

        self.objects_of_type: Dict[str, List[str]] = {}
        for obj, typ in problem.objects.items():
            for t in domain.supertypes.get(typ, {typ, "object"}):
                self.objects_of_type.setdefault(t, []).append(obj)
        self.objects_of_type.setdefault("object", list(problem.objects))
        for k in self.objects_of_type:
            self.objects_of_type[k].sort()

        self.atom_ids: Dict[Tuple[str, ...], int] = {}
        self.atoms: List[Tuple[str, ...]] = []
        self.ground_actions: List[GroundAction] = []
        self.raw_ground_count = 0
        for act in domain.actions:
            self._ground_action(act)
        self.init_state = frozenset(self.atom_id(a) for a in problem.init if a[0] in fluent_preds)
        self.goal = self._ground_formula(problem.goal, {})
        self._build_index()

    # -- atoms --------------------------------------------------------------
    def atom_id(self, atom: Tuple[str, ...]) -> int:
        aid = self.atom_ids.get(atom)
        if aid is None:
            aid = len(self.atoms)
            self.atom_ids[atom] = aid
            self.atoms.append(atom)
        return aid

    # -- 3-valued evaluation with partial binding (statics only) -----------
    def _eval_partial(self, f, binding: Dict[str, str]) -> Optional[bool]:
        head = f[0]
        if head == "and":
            res: Optional[bool] = True
            for sub in f[1:]:
                v = self._eval_partial(sub, binding)
                if v is False:
                    return False
                if v is None:
                    res = None
            return res
        if head == "or":
            res = False
            for sub in f[1:]:
                v = self._eval_partial(sub, binding)
                if v is True:
                    return True
                if v is None:
                    res = None
            return res
        if head == "not":
            v = self._eval_partial(f[1], binding)
            return None if v is None else (not v)
        if head == "imply":
            a = self._eval_partial(f[1], binding)
            b = self._eval_partial(f[2], binding)
            if a is False or b is True:
                return True
            if a is True and b is False:
                return False
            return None
        if head in ("forall", "exists"):
            return None
        if head == "=":
            x, y = _subst(f[1], binding), _subst(f[2], binding)
            if x.startswith("?") or y.startswith("?"):
                return None
            return x == y
        if head not in self.fluent_preds:
            args = [_subst(a, binding) for a in f[1:]]
            if any(a.startswith("?") for a in args):
                return None
            return (head, *args) in self.static
        return None

    def _lit_candidates(self, lit, var: str, binding: Dict[str, str]) -> Optional[Set[str]]:
        """Objects var can take so that the static literal lit may hold (None: no bound).

        Handles static atoms whose other arguments are bound, conjunctions
        (intersection) and disjunctions (union, only if every disjunct bounds
        var - e.g. the adjacency test of the move actions)."""
        if not isinstance(lit, list) or not lit:
            return None
        head = lit[0]
        if head in ("and", "or"):
            subs = [self._lit_candidates(sub, var, binding) for sub in lit[1:]]
            if head == "and":
                known = [s for s in subs if s is not None]
                if not known:
                    return None
                out = known[0]
                for s in known[1:]:
                    out = out & s
                return out
            if not subs or any(s is None for s in subs):
                return None
            return set().union(*subs)
        if head in ("not", "forall", "exists", "imply", "when", "="):
            return None
        if head in self.fluent_preds or var not in lit[1:]:
            return None
        args = [_subst(a, binding) for a in lit[1:]]
        pos_var = [i for i, a in enumerate(lit[1:]) if a == var]
        # Atoms that agree with the bound arguments (other unbound variables
        # are projected away), e.g. (marks ?c ?m1 ?m2 ?m3 ?m4) with ?c bound
        # gives ?m1 a single candidate.
        atoms: Optional[Set[Tuple[str, ...]]] = None
        for i, a in enumerate(args):
            if a.startswith("?"):
                continue
            s = self.static_index.get((lit[0], i, a), set())
            atoms = s if atoms is None else atoms & s
        if atoms is None:
            if any(a.startswith("?") and a != var for a in args):
                # nothing bound and other free variables: projecting every
                # atom of the predicate costs more than it prunes
                return None
            atoms = self.static_by_pred.get(lit[0], set())
        return {atom[1 + pos_var[0]] for atom in atoms
                if all(atom[1 + i] == atom[1 + pos_var[0]] for i in pos_var[1:])}

    def _candidates(self, pre, var: str, typ: str, binding: Dict[str, str]) -> Iterable[str]:
        """Candidate objects for var from top-level static conjuncts."""
        domain = self.objects_of_type.get(typ, [])
        best = self._lit_candidates(pre if pre and pre[0] == "and" else ["and", pre], var, binding)
        if best is None:
            return domain
        dom_set = set(domain)
        return sorted(o for o in best if o in dom_set)

    def _ground_action(self, act: Action) -> None:
        params = act.params
        names = [p for p, _ in params]
        types = dict(params)
        # Top-level conjuncts with their variables: after binding a parameter,
        # only the conjuncts that mention it are re-checked against the static
        # facts (re-evaluating the whole precondition at every partial binding
        # dominated grounding time).
        conj = act.pre[1:] if act.pre and act.pre[0] == "and" else [act.pre]
        checks = [(c, _free_vars(c)) for c in conj
                  if isinstance(c, list) and c and c[0] not in ("forall", "exists")]

        def rec(binding: Dict[str, str], remaining: List[str]):
            if not remaining:
                yield dict(binding)
                return
            # choose most constrained remaining parameter
            best_var, best_cands = None, None
            for v in remaining:
                cands = self._candidates(act.pre, v, types[v], binding)
                cands = list(cands)
                if best_cands is None or len(cands) < len(best_cands):
                    best_var, best_cands = v, cands
                    if len(cands) <= 1:
                        break
            rest = [v for v in remaining if v != best_var]
            ready = [c for c, vs in checks if best_var in vs]
            for obj in best_cands:
                binding[best_var] = obj
                if all(self._eval_partial(c, binding) is not False for c in ready):
                    yield from rec(binding, rest)
                del binding[best_var]

        for binding in rec({}, list(names)):
            pre = self._ground_formula(act.pre, binding)
            if pre is FALSE:
                continue
            self.raw_ground_count += 1
            effs: List[Tuple[object, Tuple[int, ...], Tuple[int, ...]]] = []
            self._ground_effect(act.eff, binding, TRUE, effs)
            label = "(" + " ".join([act.name] + [binding[n] for n in names]) + ")"
            self.ground_actions.append(GroundAction(label, act.name, pre, effs))

    def _ground_formula(self, f, binding: Dict[str, str]):
        head = f[0]
        if head in ("and", "or"):
            subs = []
            for sub in f[1:]:
                g = self._ground_formula(sub, binding)
                if head == "and":
                    if g is FALSE:
                        return FALSE
                    if g is TRUE:
                        continue
                else:
                    if g is TRUE:
                        return TRUE
                    if g is FALSE:
                        continue
                subs.append(g)
            if not subs:
                return TRUE if head == "and" else FALSE
            if len(subs) == 1:
                return subs[0]
            return (head, tuple(subs))
        if head == "not":
            g = self._ground_formula(f[1], binding)
            if g is TRUE:
                return FALSE
            if g is FALSE:
                return TRUE
            return ("not", g)
        if head == "imply":
            return self._ground_formula(["or", ["not", f[1]], f[2]], binding)
        if head in ("forall", "exists"):
            qvars = _typed_list(f[1])
            parts = []
            for objs in itertools.product(*[self.objects_of_type.get(t, []) for _, t in qvars]):
                b = dict(binding)
                b.update({v: o for (v, _), o in zip(qvars, objs)})
                parts.append(self._ground_formula(f[2], b))
            # reuse and/or simplification
            return self._combine("and" if head == "forall" else "or", parts)
        if head == "=":
            return TRUE if _subst(f[1], binding) == _subst(f[2], binding) else FALSE
        atom = (head, *[_subst(a, binding) for a in f[1:]])
        if head not in self.fluent_preds:
            return TRUE if atom in self.static else FALSE
        return ("atom", self.atom_id(atom))

    @staticmethod
    def _combine(op: str, parts):
        subs = []
        for g in parts:
            if op == "and":
                if g is FALSE:
                    return FALSE
                if g is TRUE:
                    continue
            else:
                if g is TRUE:
                    return TRUE
                if g is FALSE:
                    continue
            subs.append(g)
        if not subs:
            return TRUE if op == "and" else FALSE
        return subs[0] if len(subs) == 1 else (op, tuple(subs))

    def _ground_effect(self, e, binding, cond, out) -> None:
        head = e[0]
        if head == "and":
            for sub in e[1:]:
                self._ground_effect(sub, binding, cond, out)
            return
        if head in ("increase", "decrease", "assign"):
            return
        if head == "forall":
            qvars = _typed_list(e[1])
            for objs in itertools.product(*[self.objects_of_type.get(t, []) for _, t in qvars]):
                b = dict(binding)
                b.update({v: o for (v, _), o in zip(qvars, objs)})
                self._ground_effect(e[2], b, cond, out)
            return
        if head == "when":
            c = self._ground_formula(e[1], binding)
            c = self._combine("and", [cond, c])
            if c is FALSE:
                return
            self._ground_effect(e[2], binding, c, out)
            return
        if head == "not":
            atom = (e[1][0], *[_subst(a, binding) for a in e[1][1:]])
            out.append((cond, (), (self.atom_id(atom),)))
            return
        atom = (head, *[_subst(a, binding) for a in e[1:]])
        out.append((cond, (self.atom_id(atom),), ()))

    # -- execution -------------------------------------------------------------
    def _build_index(self) -> None:
        init_counts: Dict[str, int] = {}
        for aid in self.init_state:
            p = self.atoms[aid][0]
            init_counts[p] = init_counts.get(p, 0) + 1
        self.index: Dict[int, List[GroundAction]] = {}
        self.unindexed: List[GroundAction] = []
        conj_keys = []
        freq: Counter = Counter()
        for ga in self.ground_actions:
            conj = ga.pre[1] if ga.pre[0] == "and" else (ga.pre,)
            keys = [g[1] for g in conj if g[0] == "atom"]
            conj_keys.append(keys)
            freq.update(keys)
        for ga, keys in zip(self.ground_actions, conj_keys):
            if not keys:
                self.unindexed.append(ga)
                continue
            # Index under the most selective precondition atom: the one shared
            # by the fewest actions (a nullary phase flag such as check_fall is
            # shared by thousands and would make every lookup test them all).
            key = min(keys, key=lambda a: (freq[a], init_counts.get(self.atoms[a][0], 0), a))
            self.index.setdefault(key, []).append(ga)
        self.index_keys = frozenset(self.index)

    def applicable(self, state: FrozenSet[int], pred=None) -> List["GroundAction"]:
        out = []
        for aid in self.index_keys & state:
            for ga in self.index[aid]:
                if (pred is None or pred(ga)) and holds(ga.pre, state):
                    out.append(ga)
        for ga in self.unindexed:
            if (pred is None or pred(ga)) and holds(ga.pre, state):
                out.append(ga)
        return out

    def atom_str(self, aid: int) -> str:
        return "(" + " ".join(self.atoms[aid]) + ")"


@dataclass
class GroundAction:
    label: str
    schema: str
    pre: object
    effs: List[Tuple[object, Tuple[int, ...], Tuple[int, ...]]] = field(default_factory=list)

    def apply(self, state: FrozenSet[int]) -> FrozenSet[int]:
        adds: Set[int] = set()
        dels: Set[int] = set()
        for cond, add, dele in self.effs:
            if cond is TRUE or holds(cond, state):
                adds.update(add)
                dels.update(dele)
        return frozenset((state - dels) | adds)


def holds(f, state: FrozenSet[int]) -> bool:
    head = f[0]
    if head == "atom":
        return f[1] in state
    if head == "and":
        return all(holds(g, state) for g in f[1])
    if head == "or":
        return any(holds(g, state) for g in f[1])
    if head == "not":
        return not holds(f[1], state)
    if head == "true":
        return True
    if head == "false":
        return False
    raise ValueError(f"bad formula {f!r}")


def load_task(domain_text: str, problem_text: str) -> Task:
    return Task(parse_domain(domain_text), parse_problem(problem_text))


# --------------------------------------------------------------------------
# Size statistics (approximating what Fast Downward's translator produces)
# --------------------------------------------------------------------------


def _dnf(f) -> List[Tuple[FrozenSet[int], FrozenSet[int]]]:
    """DNF of a ground formula as (positive atoms, negative atoms) pairs."""
    head = f[0]
    if head == "true":
        return [(frozenset(), frozenset())]
    if head == "false":
        return []
    if head == "atom":
        return [(frozenset([f[1]]), frozenset())]
    if head == "not":
        g = f[1]
        if g[0] == "atom":
            return [(frozenset(), frozenset([g[1]]))]
        if g[0] == "not":
            return _dnf(g[1])
        if g[0] == "and":
            return _dnf(("or", tuple(("not", x) for x in g[1])))
        if g[0] == "or":
            return _dnf(("and", tuple(("not", x) for x in g[1])))
        return _dnf(TRUE if g[0] == "false" else FALSE)
    if head == "or":
        out = []
        for g in f[1]:
            out.extend(_dnf(g))
        return out
    if head == "and":
        acc = [(frozenset(), frozenset())]
        for g in f[1]:
            nxt = []
            for p1, n1 in acc:
                for p2, n2 in _dnf(g):
                    p, n = p1 | p2, n1 | n2
                    if p & n:
                        continue
                    nxt.append((p, n))
            acc = nxt
        return acc
    raise ValueError(head)


def task_stats(task: "Task") -> Dict[str, float]:
    """Relaxed-reachability-pruned operator counts, FD style.

    Disjunctive preconditions are split into one operator per DNF disjunct
    (as FD's translator does); operators whose positive preconditions are not
    relaxed-reachable from the initial state are dropped.  Negative literals
    are ignored for reachability (also as in FD)."""
    ops = []
    for ga in task.ground_actions:
        for pos, neg in _dnf(ga.pre):
            ops.append((ga, pos, neg))
    reached: Set[int] = set(task.init_state)
    changed = True
    alive = [False] * len(ops)
    while changed:
        changed = False
        for i, (ga, pos, _neg) in enumerate(ops):
            if alive[i] or not pos <= reached:
                continue
            alive[i] = True
            changed = True
            for cond, add, _dele in ga.effs:
                if add and (cond is TRUE or any(p <= reached for p, _ in _dnf(cond))):
                    reached.update(add)
        # loop until fixpoint
    live = [ops[i] for i in range(len(ops)) if alive[i]]
    n_pre = sum(len(p) + len(n) for _, p, n in live)
    n_neg = sum(len(n) for _, _, n in live)
    n_eff = sum(sum(len(a) + len(d) for _, a, d in ga.effs) for ga, _, _ in live)
    n_cond = sum(sum(1 for c, _, _ in ga.effs if c is not TRUE) for ga, _, _ in live)
    schemas = Counter(ga.schema for ga, _, _ in live)
    return {
        "operators": len(live),
        "pre_literals": n_pre,
        "neg_pre_literals": n_neg,
        "effect_literals": n_eff,
        "cond_effects": n_cond,
        "reachable_atoms": len(reached),
        "schemas": dict(schemas),
    }

