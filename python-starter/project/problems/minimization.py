import argparse
from collections import deque

from project.problem import Problem


class MinimizationProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--mini',
            help='A bemeneti automatát minimalizálja',
            action='store_true'
        )

    def is_chosen_problem(self, args) -> bool:
        return args.mini

    def run(self, args):
        if not args.input or not args.output:
            raise ValueError('A --mini használatához a --input és a --output megadása is kötelező.')

        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.read().splitlines()

        if len(lines) < 4:
            raise ValueError('A bemeneti fájlnak legalább négy fejlécsort kell tartalmaznia.')

        states = lines[0].split()
        alphabet = sorted(lines[1].split())
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
            raise ValueError(f'Ismeretlen végállapot(ok): {", ".join(invalid_states)}.')

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

            key = (source, symbol)
            if key in transitions and transitions[key] != destination:
                raise ValueError(
                    f'A(z) {line_number}. sor nem determinisztikus átmenetet ad meg: '
                    f'{source} {symbol}.'
                )
            transitions[key] = destination

        start_state = start_state_parts[0]
        implicit_sink = object()

        def destination(state, symbol):
            if state is implicit_sink:
                return implicit_sink
            return transitions.get((state, symbol), implicit_sink)

        reachable = []
        reachable_set = {start_state}
        pending = deque([start_state])
        while pending:
            state = pending.popleft()
            reachable.append(state)
            for symbol in alphabet:
                target = destination(state, symbol)
                if target not in reachable_set:
                    reachable_set.add(target)
                    pending.append(target)

        partitions = []
        for is_accepting in (True, False):
            block = [
                state for state in reachable
                if (state in accepting_states) == is_accepting
            ]
            if block:
                partitions.append(block)

        while True:
            block_indices = {
                state: index
                for index, block in enumerate(partitions)
                for state in block
            }
            refined = []
            changed = False
            for block in partitions:
                groups = {}
                for state in block:
                    signature = tuple(
                        block_indices[destination(state, symbol)]
                        for symbol in alphabet
                    )
                    groups.setdefault(signature, []).append(state)
                refined.extend(groups.values())
                changed = changed or len(groups) > 1
            partitions = refined
            if not changed:
                break

        state_order = {state: index for index, state in enumerate(states)}

        def renamed(state):
            if state.startswith('q') and state[1:].isdigit():
                suffix = state[1:]
            else:
                suffix = str(state_order[state])
            return f's{suffix}'

        output_names = {}
        for index, block in enumerate(partitions):
            real_states = [state for state in block if state is not implicit_sink]
            if real_states:
                representative = min(real_states)
                output_names[index] = renamed(representative)

        output_states = sorted(output_names.values())
        start_block = next(
            index for index, block in enumerate(partitions)
            if start_state in block
        )
        output_start_state = output_names[start_block]

        output_accepting_states = sorted(
            output_names[index]
            for index, block in enumerate(partitions)
            if output_names.get(index) is not None
            and any(state in accepting_states for state in block)
        )

        transitions_to_write = set()
        for index, block in enumerate(partitions):
            if index not in output_names:
                continue
            for symbol in alphabet:
                targets = {
                    block_indices[target]
                    for state in block
                    if state is not implicit_sink
                    and (target := transitions.get((state, symbol))) is not None
                }
                for target_block in targets:
                    if target_block in output_names:
                        transitions_to_write.add((
                            output_names[index],
                            symbol,
                            output_names[target_block]
                        ))

        output_lines = [
            ' '.join(output_states),
            ' '.join(alphabet),
            output_start_state,
            ' '.join(output_accepting_states),
        ]
        output_lines.extend(
            f'{source} {symbol} {target}'
            for source, symbol, target in sorted(transitions_to_write)
        )

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(output_lines) + '\n')
