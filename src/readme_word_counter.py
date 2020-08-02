from __future__ import absolute_import

import argparse
import logging
import re
import os

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.metrics import Metrics
from git_handler import GitHandler

FORMAT = '%(asctime)-15s %(levelname)s  ||  %(module)-20s : %(message)s'
LOG_FILE_NAME = 'Logs.log'
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(CURRENT_PATH, "..", "logs", LOG_FILE_NAME)
OUTPUT_PATH = os.path.join(CURRENT_PATH, "..", 'archive', 'output')
logging.basicConfig(filename=LOG_PATH, format=FORMAT, level=logging.INFO)


class ReadmeExtractionDoFn(beam.DoFn):
    """
    extract readme content from each repository.
    """
    def __init__(self):
        beam.DoFn.__init__(self)
        self.no_readme = Metrics.counter(self.__class__, 'no_readme')

    def process(self, element, *args, **kwargs):
        git_handler = GitHandler(element)
        readme_content = git_handler.extract_readme_content()
        if readme_content:
            return [readme_content]
        else:
            self.no_readme.inc()
            return []


class WordExtractingDoFn(beam.DoFn):
    """
    Parse each readme content into words.
    """
    def __init__(self):
        beam.DoFn.__init__(self)

    def process(self, element, *args, **kwargs):
        text_line = element.strip()
        words = re.findall(r'[\w\']+', text_line, re.UNICODE)
        return words


def run(argv=None, save_main_session=True):
    """
    Main entry point; defines and runs the wordcount pipeline.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        dest='input',
        default="",  # default is an empty list
        help='Input file to process.')
    known_args, pipeline_args = parser.parse_known_args(argv)
    # run with direct runner
    pipeline_args.extend([
        '--runner=DirectRunner',
    ])
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
    with beam.Pipeline(options=pipeline_options) as p:
        repos_list = known_args.input.split(",")
        repos = p | beam.Create(repos_list)
        # get the readme files content
        contents = repos | 'ReadmeContent' >> (beam.ParDo(ReadmeExtractionDoFn()).with_output_types(unicode))
        # Count the occurrences of each word
        counts = (
            contents
            | 'split' >>
            (beam.ParDo(WordExtractingDoFn()).with_output_types(unicode))
            | 'PairWithOne' >>
            beam.Map(lambda x: (x, 1))
            | 'GroupAndSum' >> beam.CombinePerKey(sum))

        # Format the counts into a PCollection of strings.
        def format_result(word_count):
            (word, count) = word_count
            return '%s: %s' % (word, count)
        output = counts | 'Format' >> beam.Map(format_result)
        # write the output
        output | WriteToText(OUTPUT_PATH)


if __name__ == '__main__':
    run()
