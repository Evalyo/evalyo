import glob
import os
import sys

from django.conf import settings
from django.core.management import CommandError
from django.core.management.commands.makemessages import Command as MakeMessagesCommand
from django.core.management.commands.makemessages import check_programs

from judge.models import NavigationBar, ProblemType


class Command(MakeMessagesCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--locale",
            "-l",
            default=[],
            dest="locale",
            action="append",
            help="Creates or updates the message files for the given locale(s) (e.g. pt_BR). "
            "Can be used multiple times.",
        )
        parser.add_argument(
            "--exclude",
            "-x",
            default=[],
            dest="exclude",
            action="append",
            help="Locales to exclude. Default is none. Can be used multiple times.",
        )
        parser.add_argument(
            "--all",
            "-a",
            action="store_true",
            dest="all",
            default=False,
            help="Updates the message files for all existing locales.",
        )
        parser.add_argument(
            "--no-wrap",
            action="store_true",
            dest="no_wrap",
            default=False,
            help="Don't break long message lines into several lines.",
        )
        parser.add_argument(
            "--no-obsolete",
            action="store_true",
            dest="no_obsolete",
            default=False,
            help="Remove obsolete message strings.",
        )
        parser.add_argument(
            "--keep-pot",
            action="store_true",
            dest="keep_pot",
            default=False,
            help="Keep .pot file after making messages. Useful when debugging.",
        )

    def handle(self, *args, **options):
        # Setup basic configuration
        self._setup_basic_config(options)

        # Configure i18n and message options
        self._configure_i18n()
        self._setup_message_options(options)

        # Setup locale paths and validate arguments
        locale = options.get("locale")
        exclude = options.get("exclude")
        process_all = options.get("all")
        self._validate_arguments(locale, exclude, process_all)
        self._setup_locale_paths()

        # Build and filter locale list
        locales = self._build_locale_list(locale, exclude, process_all)

        # Check required programs
        if locales:
            check_programs("msguniq", "msgmerge", "msgattrib")
        check_programs("xgettext")

        # Process potfiles
        self._process_potfiles(locales)

    def _setup_basic_config(self, options):
        """Setup basic configuration from options."""
        self.domain = "dmoj-user"
        self.verbosity = options.get("verbosity")
        self.no_obsolete = options.get("no_obsolete")
        self.keep_pot = options.get("keep_pot")

    def _configure_i18n(self):
        """Ensure that the i18n framework is enabled."""
        if settings.configured:
            settings.USE_I18N = True
        else:
            settings.configure(USE_I18N=True)

    def _setup_message_options(self, options):
        """Setup message formatting options to avoid messing with mutable class variables."""
        if options.get("no_wrap"):
            self.msgmerge_options = self.msgmerge_options[:] + ["--no-wrap"]
            self.msguniq_options = self.msguniq_options[:] + ["--no-wrap"]
            self.msgattrib_options = self.msgattrib_options[:] + ["--no-wrap"]
            self.xgettext_options = self.xgettext_options[:] + ["--no-wrap"]
        if options.get("no_location"):
            self.msgmerge_options = self.msgmerge_options[:] + ["--no-location"]
            self.msguniq_options = self.msguniq_options[:] + ["--no-location"]
            self.msgattrib_options = self.msgattrib_options[:] + ["--no-location"]
            self.xgettext_options = self.xgettext_options[:] + ["--no-location"]

    def _validate_arguments(self, locale, exclude, process_all):
        """Validate command arguments."""
        if locale is None and not exclude and not process_all:
            raise CommandError(f"Type '{os.path.basename(sys.argv[0])} help {sys.argv[1]}' for usage information.")

    def _setup_locale_paths(self):
        """Setup locale paths for message processing."""
        self.invoked_for_django = False
        self.locale_paths = []
        self.default_locale_path = None

        if os.path.isdir(os.path.join("conf", "locale")):
            self.locale_paths = [os.path.abspath(os.path.join("conf", "locale"))]
            self.default_locale_path = self.locale_paths[0]
            self.invoked_for_django = True
        else:
            self.locale_paths.extend(settings.LOCALE_PATHS)
            # Allow to run makemessages inside an app dir
            if os.path.isdir("locale"):
                self.locale_paths.append(os.path.abspath("locale"))
            if self.locale_paths:
                self.default_locale_path = self.locale_paths[0]
                if not os.path.exists(self.default_locale_path):
                    os.makedirs(self.default_locale_path)

    def _build_locale_list(self, locale, exclude, process_all):
        """Build and filter the list of locales to process."""
        # Build locale list
        locale_dirs = list(filter(os.path.isdir, glob.glob(f"{self.default_locale_path}/*")))
        all_locales = list(map(os.path.basename, locale_dirs))

        # Account for excluded locales
        if process_all:
            locales = all_locales
        else:
            locales = locale or all_locales
            locales = set(locales) - set(exclude)

        return locales

    def _process_potfiles(self, locales):
        """Process potfiles for each locale."""
        try:
            potfiles = self.build_potfiles()

            # Build po files for each selected locale
            for locale in locales:
                if self.verbosity > 0:
                    self.stdout.write(f"processing locale {locale}\n")
                for potfile in potfiles:
                    self.write_po_file(potfile, locale)
        finally:
            if not self.keep_pot:
                self.remove_potfiles()

    def find_files(self, root):
        return []

    def _emit_message(self, potfile, string):
        potfile.write(
            """
msgid "{}"
msgstr ""
""".format(string.replace("\\", r"\\").replace("\t", "\\t").replace("\n", "\\n").replace('"', '\\"'))
        )

    def process_files(self, file_list):
        with open(os.path.join(self.default_locale_path, "dmoj-user.pot"), "w", encoding="utf-8") as potfile:
            if self.verbosity > 1:
                self.stdout.write("processing navigation bar")
            for label in NavigationBar.objects.values_list("label", flat=True):
                if self.verbosity > 2:
                    self.stdout.write(f'processing navigation item label "{label}"\n')
                self._emit_message(potfile, label)

            if self.verbosity > 1:
                self.stdout.write("processing problem types")
            for name in ProblemType.objects.values_list("full_name", flat=True):
                if self.verbosity > 2:
                    self.stdout.write(f'processing problem type name "{name}"\n')
                self._emit_message(potfile, name)
