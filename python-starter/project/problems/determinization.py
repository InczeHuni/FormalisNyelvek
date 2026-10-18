import argparse
from collections import deque

from project.problem import Problem


class DeterminizationProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--det',
            help='A bemeneti automatát determinisztikussá alakítja',
            action='store_true'
        )

    def is_chosen_problem(self, args) -> bool:
        return args.det

    def run(self, args):
        if not args.input or not args.output:
            raise ValueError('A --det használatához a --input és a --output megadása is kötelező.')

        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.read().splitlines()

        if len(lines) < 4:
            raise ValueError('A bemeneti fájlnak legalább négy fejlécsort kell tartalmaznia.')

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state_parts = lines[2].split()
        accepting_states = set(lines[3].split())

        if not states:
            raise ValueError('Az állapotok listája nem lehet üres.')
        if len(states) != len(set(states)):
            raise ValueError('Az állapotok listája nem tartalmazhat duplikátumot.')
        if len(alphabet) != len(set(alphabet)):
            raise ValueError('Az ábécé listája nem tartalmazhat duplikátumot.')
        if len(start_state_parts) != 1 or start_state_parts[0] not in states:
            raise ValueError('A kezdőállapotnak pontosan egy, a felsorolt állapotok között szereplő állapotnak kell lennie.')
        if not accepting_states.issubset(states):
            invalid_states = sorted(accepting_states.difference(states))
            raise ValueError(
                f'Ismeretlen végállapot(ok): {", ".join(invalid_states)}.'
            )

        transitions = {}
        for line_number, line in enumerate(lines[4:], start=5):
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 3:
                raise ValueError(
                    f'Hibás átmenet a(z) {line_number}. sorban: három elemet kell megadni.'
                )

            source, symbol, destination = parts
            if source not in states:
                raise ValueError(
                    f'Ismeretlen kiinduló állapot a(z) {line_number}. sorban: {source}.'
                )
            if symbol not in alphabet:
                raise ValueError(
                    f'Ismeretlen ábécéjel a(z) {line_number}. sorban: {symbol}.'
                )
            if destination not in states:
                raise ValueError(
                    f'Ismeretlen célállapot a(z) {line_number}. sorban: {destination}.'
                )

            transitions.setdefault((source, symbol), set()).add(destination)

        initial_subset = frozenset(start_state_parts)
        subsets = [initial_subset]
        subset_names = {initial_subset: 's0'}
        pending_subsets = deque([initial_subset])
        deterministic_transitions = []

        while pending_subsets:
            current_subset = pending_subsets.popleft()
            current_name = subset_names[current_subset]

            for symbol in alphabet:
                destination_subset = frozenset(
                    destination
                    for state in current_subset
                    for destination in transitions.get((state, symbol), ())
                )
                if not destination_subset:
                    continue

                if destination_subset not in subset_names:
                    subset_names[destination_subset] = f's{len(subsets)}'
                    subsets.append(destination_subset)
                    pending_subsets.append(destination_subset)

                deterministic_transitions.append(
                    (current_name, symbol, subset_names[destination_subset])
                )

        deterministic_states = [subset_names[subset] for subset in subsets]
        deterministic_accepting_states = [
            subset_names[subset]
            for subset in subsets
            if not subset.isdisjoint(accepting_states)
        ]

        output_lines = [
            ' '.join(deterministic_states),
            ' '.join(alphabet),
            's0',
            ' '.join(deterministic_accepting_states),
        ]
        output_lines.extend(
            f'{source} {symbol} {destination}'
            for source, symbol, destination in deterministic_transitions
        )

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(output_lines) + '\n')
