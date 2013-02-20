import logging
import os
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from xml.etree import ElementTree

log = logging.getLogger(__name__)


class Phpcs(Tool):

    name = 'phpcs'

    def check_dependencies(self):
        """
        See if phpcs is on the system path.
        """
        return in_path('phpcs')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.php'

    def process_files(self, files):
        """
        Run code checks with phpcs.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['phpcs', '--report=checkstyle']

        standard = 'PEAR'
        if self.options.get('standard'):
            standard = self.options['standard']
        extension = 'php'
        if self.options.get('extensions'):
            extension = self.options['extensions']
        command += ['--standard=' + standard]
        command += ['--extensions=' + extension]
        if self.options.get('tab_width'):
            command += ['--tab-width=' + self.options['tab_width']]
        command += files
        output = run_command(
            command,
            ignore_error=True)
        try:
            tree = ElementTree.fromstring(output)
        except:
            log.error("Unable to parse XML from phpcs")
            raise

        # Parse checkstyle.xml
        # This might be good for refactoring later.
        for f in tree.iter('file'):
            filename = self._get_filename(f.get('name'), files)
            for err in f.iter('error'):
                self.problems.add(
                    filename,
                    int(err.get('line')),
                    err.get('message'))

    def _get_filename(self, name, files):
        """
        PHPCS converts filenames to absolute paths.
        Convert each of the files in `files` to an
        absolute path to locate the filename
        """
        for f in files:
            abs_path = os.path.realpath(f)
            if abs_path == name:
                return f
        msg = "Could not locate '%s' in changed files." % (name, )
        raise ValueError(msg)