from __future__ import absolute_import

import argparse
import logging
import re
import os

from past.builtins import unicode

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.io import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.metrics import Metrics
from apache_beam.metrics.metric import MetricsFilter
from git_handler import GitHandler

FORMAT = '%(asctime)-15s %(levelname)s  ||  %(module)-20s : %(message)s'
LOG_FILE_NAME = 'Logs.log'
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(CURRENT_PATH, "logs", LOG_FILE_NAME)
OUTPUT_PATH = os.path.join(CURRENT_PATH, 'archive', 'output')
logging.basicConfig(filename=LOG_PATH, format=FORMAT, level=logging.INFO)


class ReadmeExtractionDoFn(beam.DoFn):
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
  """Parse each readme content into words."""
  def __init__(self):
    beam.DoFn.__init__(self)

  def process(self, element):
    """Returns an iterator over the words of this element.
    The element is a line of text.  If the line is blank, note that, too.
    Args:
      element: the element being processed
    Returns:
      The processed element.
    """
    text_line = element.strip()
    words = re.findall(r'[\w\']+', text_line, re.UNICODE)

    return words


def run(argv=None, save_main_session=True):
    """Main entry point; defines and runs the wordcount pipeline."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        dest='input',
        default=[],  # default is an empty list
        help='Input file to process.')
    parser.add_argument(
        '--output',
        dest='output',
        default=OUTPUT_PATH,
        help='Output file to write results to.')
    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_args.extend([
        '--runner=DirectRunner',
    ])
    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session
    with beam.Pipeline(options=pipeline_options) as p:

        # Read the text file[pattern] into a PCollection.
        # lines = p | ReadFromText(known_args.input)
        #  read from List
        #["https://github.com/octocat/hello-world", "https://github.com/matiassingers/awesome-readme", "https://github.com/stayawayinesctec/stayaway-app"]
        repos_list = known_args.input.split(",")
        if len(repos_list) == 0:
            logging.error("there are no repositories")
            return None
        repos = p | beam.Create(repos_list)
        # get repos content
        contents = repos | 'ReadmeContent' >> (beam.ParDo(ReadmeExtractionDoFn()).with_output_types(unicode))
        # Count the occurrences of each word.
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

        # Write the output using a "Write" transform that has side effects.
        # pylint: disable=expression-not-assigned
        output | WriteToText(known_args.output)


if __name__ == '__main__':
    run()
