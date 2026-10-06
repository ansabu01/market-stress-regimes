use Cwd;
use File::Copy;

$pdf_mode = 1;

# Put temporary files in build/
$aux_dir = 'build';

# Keep the final PDF in report/
$out_dir = '.';

# Make BibTeX find references.bib from the report/ folder
ensure_path('BIBINPUTS', cwd());

# MiKTeX's BibTeX (0.99) cannot resolve references.bib through BIBINPUTS when the
# absolute project path contains spaces (e.g. "Semester Two"). latexmk runs
# BibTeX inside the aux dir, so copy the database there to be opened locally with
# no search path. Re-copied on every run, so edits to references.bib are always
# picked up and `latexmk -C` stays safe.
mkdir($aux_dir) unless -d $aux_dir;
copy('references.bib', "$aux_dir/references.bib") if -e 'references.bib';
