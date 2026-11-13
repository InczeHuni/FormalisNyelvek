import argparse
import re

from project.problem import Problem


LOG_PATTERN = re.compile(
    r'^([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) '
    r'([IDVEFAW]) (.+?):(?: (.*))?\r?\n?$'
)
DATE_1015_PATTERN = re.compile(r'^10-15 [0-9:.]+$')
TIME_101851_PATTERN = re.compile(r'^10-15 10:18:51(?:\.[0-9]+)?$')
SECOND_51_PATTERN = re.compile(
    r'^[0-9-]+ [0-9]{2}:[0-9]{2}:51(?:\.[0-9]+)?$'
)
LOWMEMORYKILLER_PATTERN = re.compile(r'lowmemorykiller')
EXOPLAYER_PATTERN = re.compile(r'ExoPlayer')
JAVA_POSITION_PATTERN = re.compile(r'[A-Za-z0-9_$.-]+\.java:')
JAVA_FILENAME_PATTERN = re.compile(r'([A-Za-z0-9_$-]+\.java):')
THREAD_PATTERN = re.compile(r'\bThread\b')
PACKAGE_MANAGER_PATTERN = re.compile(r'PackageManager')


class RegexProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--rgx',
            type=int,
            choices=(1, 2, 3, 4, 5),
            help='select the regex task to run',
        )

    def is_chosen_problem(self, args):
        return args.rgx is not None

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.readlines()

        if args.rgx == 1:
            results = self._count_matches(lines)
        elif args.rgx == 2:
            results = self._error_sources(lines)
        elif args.rgx == 3:
            results = self._process_ids(lines)
        elif args.rgx == 4:
            results = self._process_with_most_errors(lines)
        else:
            results = self._main_thread_error_count(lines)

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(results))

    def _count_matches(self, lines):
        counts = [0] * 10
        for line in lines:
            record = LOG_PATTERN.match(line)
            if record is None:
                continue

            timestamp, _, _, level, tag, message = record.groups()
            message = message or ''
            if DATE_1015_PATTERN.search(timestamp):
                counts[0] += 1
            if TIME_101851_PATTERN.search(timestamp):
                counts[1] += 1
            if SECOND_51_PATTERN.search(timestamp):
                counts[2] += 1
            if LOWMEMORYKILLER_PATTERN.search(tag):
                counts[3] += 1
            if TIME_101851_PATTERN.search(timestamp) and re.fullmatch(
                r'221', record.group(2)
            ):
                counts[4] += 1
            if re.fullmatch(r'E', level):
                counts[5] += 1
            if re.fullmatch(r'W', level) and PACKAGE_MANAGER_PATTERN.fullmatch(tag):
                counts[6] += 1
            if re.fullmatch(r'D', level) and EXOPLAYER_PATTERN.search(tag):
                counts[7] += 1
            if re.fullmatch(r'[EW]', level) and JAVA_POSITION_PATTERN.search(message):
                counts[8] += 1
            if THREAD_PATTERN.search(message):
                counts[9] += 1

        return [str(count) for count in counts]

    def _error_sources(self, lines):
        sources = []
        in_error = False
        for line in lines:
            record = LOG_PATTERN.match(line)
            if record is not None:
                in_error = re.fullmatch(r'E', record.group(4)) is not None
                message = record.group(6) or ''
                if in_error:
                    sources.extend(
                        match.group(1)
                        for match in JAVA_FILENAME_PATTERN.finditer(message)
                    )
            elif in_error:
                sources.extend(
                    match.group(1)
                    for match in JAVA_FILENAME_PATTERN.finditer(line)
                )

        return sources

    def _process_ids(self, lines):
        process_ids = {}
        for line in lines:
            record = LOG_PATTERN.match(line)
            if record is not None:
                process_ids[record.group(2)] = True
        return list(process_ids)

    def _process_with_most_errors(self, lines):
        error_counts = {}
        for line in lines:
            record = LOG_PATTERN.match(line)
            if record is not None and re.fullmatch(r'E', record.group(4)):
                process_id = record.group(2)
                error_counts[process_id] = error_counts.get(process_id, 0) + 1

        if not error_counts:
            return ['PID=0 (0 errors)']

        process_id = max(error_counts, key=error_counts.get)
        return [f'PID={process_id} ({error_counts[process_id]} errors)']

    def _main_thread_error_count(self, lines):
        count = 0
        for line in lines:
            record = LOG_PATTERN.match(line)
            if (
                record is not None
                and re.fullmatch(r'E', record.group(4))
                and re.fullmatch(record.group(2), record.group(3))
            ):
                count += 1
        return [str(count)]
