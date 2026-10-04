import argparse
from project.problem import Problem


class DFAProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """Argumentum hozzáadása a DFA ellenőrzéshez."""
        parser.add_argument(
            '--check',
            help='Vesszővel elválasztott szavak ellenőrzése az automatában',
            type=str
        )

    def is_chosen_problem(self, args) -> bool:
        """Ellenőrzi, hogy a --check paraméter meg lett-e adva."""
        return args.check is not None

    def run(self, args):
        """Futtatja a DFA szimulációt a bemeneti és kimeneti fájlok alapján."""
        input_file = args.input
        output_file = args.output
        words_to_check = [w.strip() for w in args.check.split(',')]

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) < 4:
            raise ValueError("A bemeneti fájl nem tartalmaz elegendő fejléc információt!")

        states = lines[0].split()
        alphabet = set(lines[1].split())
        start_state = lines[2]
        accept_states = set(lines[3].split())

        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) == 3:
                from_state, symbol, to_state = parts
                transitions[(from_state, symbol)] = to_state


        results = []
        for word in words_to_check:
            current_state = start_state
            is_accepted = True

            for char in word:
                if char not in alphabet or (current_state, char) not in transitions:
                    is_accepted = False
                    break
                current_state = transitions[(current_state, char)]

            if is_accepted and current_state in accept_states:
                results.append("IGEN")
            else:
                results.append("NEM")
                
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results) + '\n')