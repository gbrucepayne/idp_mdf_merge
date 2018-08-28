#!/usr/bin/env python
"""
Tool for merging Message Definition Files for Inmarsat IsatData Pro Message Gateway System.
Imports two or more XML files with extension ``.idpmsg``.

.. table:: Data Types

    +--------------+------------------+-------------+------------------------+
    | Terminal API | MDF.idpmsg       | REST API    | Note                   |
    +--------------+------------------+-------------+------------------------+
    | Enum (0)     | EnumField        | enum        |                        |
    | Boolean (1)  | BooleanField     | boolean     |                        |
    | Unsigned (2) | UnsignedIntField | unsignedint | Note: 31 bits          |
    | Signed (3)   | SignedIntField   | signedint   | Note: 32 bits          |
    | String (4)   | StringField      | string      | Note: size in chars    |
    | Data (5)     | DataField        | data        | Note: size in bytes    |
    | Array (6)    | ArrayField       | array       | Note: size in elements |
    | Dynamic (7)  | DynamicField     |             |                        |
    | Property (8) | PropertyField    |             |                        |
    | Message (9)  | MessageField     |             |                        |
    +--------------+------------------+-------------+------------------------+

.. note::
   **TODO**:

   Add log file output including any errors.

   Document steps for creating an executable application (having problems with
   `tcl on Windows 7 <https://github.com/pyinstaller/pyinstaller/issues/1957>`_...):

   * `Ref 1 <https://stackoverflow.com/questions/5458048/how-to-make-a-python-script-standalone-executable-to-run-without-any-dependency>`_
   * `Ref 2 <https://medium.com/dreamcatcher-its-blog/making-an-stand-alone-executable-from-a-python-script-using-pyinstaller-d1df9170e263>`_
   * `Ref 3 <https://ourcodeworld.com/articles/read/273/how-to-create-an-executable-exe-from-a-python-script-in-windows-using-pyinstaller>`_

   Ensure core files are included in build package or that URL links are accessible:

   * `Ref 4 <https://stackoverflow.com/questions/16334297/how-to-embed-a-text-file-into-a-single-executable-using-py2exe>`_
   * `Ref 5 <https://python-packaging.readthedocs.io/en/latest/non-code-files.html>`_

"""

__version__ = "1.1.0"

import sys
import argparse
import os
import httplib
import xml.etree.ElementTree as ET
import Tkinter as tk
import tkFileDialog
import ntpath
# ''' Workaround suggested on https://github.com/RedFantom/gsf-parser/issues/17   # DID NOT WORK!
try:
    tcl_lib = os.path.join(sys._MEIPASS, "lib")
    tcl_new_lib = os.path.join(os.path.dirname(os.path.dirname(tcl_lib)), os.path.basename(tcl_lib))
    import shutil
    shutil.copytree(src=tcl_lib, dst=tcl_new_lib)
except:
    pass
# '''

# GLOBAL DEFAULTS
CORE_MODEM_PATH = os.path.dirname(os.path.realpath(__file__))    # TODO: insert evergreen URL
CORE_MODEM_FILE = 'coremodem.idpmsg'
LSF_CORE_PATH = os.path.dirname(os.path.realpath(__file__))   # TODO: insert evergreen URL
LSF_CORE_AGENTS_FILE = 'skywave_lsf_core_agents.idpmsg'
OUTPUT_PATH = os.path.dirname(os.path.realpath(__file__))
OUTPUT_FILE = 'merged.idpmsg'

# Namespace used by SkyWave SDK
NS = {
    # 'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xsd': 'http://www.w3.org/2001/XMLSchema'
}

enable_smart_tags = False


class MergeDialog(tk.Frame):
    """
    A class to handle file selections for Message Definition mergers.

    :param master: the Tkinter root frame
    :param parameters: a dictionary structure containing merge parameters

        * ``files`` - (list of string) file/path names to merge
        * ``target`` - (string) output file/path name
        * ``modem`` - (Boolean) flag to include core modem definitions
        * ``lsf`` - (Boolead) flag to include SkyWave LSF core/agent definitions
        * ``meta`` - (Boolean) flag to include XML tag metadata (Service and Message)
        * ``error`` - (None) if no errors or (list of string) any processing errors

    """
    global enable_smart_tags

    def __init__(self, master, parameters):
        tk.Frame.__init__(self, master)
        self.master = master
        self.parameters = parameters

        self.master.title("IDP Message Definition Merge Tool")

        entry_label_width = 33

        self.input_label = tk.Label(master, text="Files to merge:")
        self.input_label.grid(row=0, column=0, sticky=tk.E)

        self.file_list = tk.Listbox(master,
                                    selectmode='extended',
                                    height=5,
                                    width=entry_label_width)
        self.file_path_list = []
        if self.parameters['files'] is not None:
            for f in self.parameters['files']:
                self.file_list.insert(tk.END, ntpath.basename(f))
                self.file_path_list.append(f)
        self.file_list.grid(row=0, column=1, rowspan=2, sticky=tk.W)

        self.add_button = tk.Button(master,
                                    text="Add File(s)...",
                                    command=self.add_message_definition_files)
        self.add_button.grid(row=0, column=2, sticky=tk.W)

        self.rem_button = tk.Button(master,
                                    text="Remove File(s)...",
                                    command=self.remove_message_definition_files)
        self.rem_button.grid(row=1, column=2, sticky=tk.W)

        self.output_label = tk.Label(master, text="Target output file:")
        self.output_label.grid(row=3, column=0, sticky=tk.E)

        self.var_target = tk.StringVar(value=OUTPUT_FILE)
        self.parameters['target'] = OUTPUT_PATH + '\\' + OUTPUT_FILE
        self.target = tk.Entry(master, textvariable=self.var_target, width=entry_label_width)
        self.target.grid(row=3, column=1, sticky=tk.W)

        self.add_target_button = tk.Button(master, text="Add Target...", command=self.add_target)
        self.add_target_button.grid(row=3, column=2, sticky=tk.W)

        self.var_modem = tk.IntVar(value=self.parameters['modem'])
        self.modem_check = tk.Checkbutton(master,
                                          text="Merge Core Modem definitions",
                                          variable=self.var_modem)
        self.modem_check.grid(row=4, column=1, sticky=tk.W)

        self.var_lsf = tk.IntVar(value=self.parameters['lsf'])
        self.lsf_core_check = tk.Checkbutton(master,
                                             text="Merge LSF Core/Agent definitions",
                                             variable=self.var_lsf)
        self.lsf_core_check.grid(row=5, column=1, sticky=tk.W)

        if enable_smart_tags:
            self.var_meta = tk.IntVar(value=self.parameters['meta'])
            self.meta_check = tk.Checkbutton(master,
                                             text="Apply metadata tags",
                                             variable=self.var_meta)
            self.meta_check.grid(row=6, column=1, sticky=tk.W)
        else:
            self.var_meta = tk.IntVar(value=False)

        self.ok_button = tk.Button(master, text="OK", command=self.ok_quit)
        self.ok_button.grid(row=8, column=1)

    def add_message_definition_files(self):
        """Opens a dialog box to import the target XML files."""
        filters = {
            # ('all files', '*.*'),
            ('idpmsg files', '*.idpmsg')
        }
        title = "Select Source File(s) to Merge..."
        file_names = tkFileDialog.askopenfilenames(title=title, filetypes=filters)
        if len(file_names) > 0:
            if self.parameters['files'] is not None:
                self.parameters['files'] = self.parameters['files'] + file_names
            else:
                self.parameters['files'] = file_names
        for f in file_names:
            self.file_list.insert(tk.END, ntpath.basename(f))
            self.file_path_list.append(f)

    def remove_message_definition_files(self):
        """Removes selected message definition files from ``files`` list."""
        for i in self.file_list.curselection():
            self.file_list.delete(i)
            self.file_path_list.pop(i)

    def add_target(self):
        """Opens a dialog box to save the target merged XML file."""
        filters = {
            # ('all files', '*.*'),
            ('idpmsg files', '*.idpmsg')
        }
        title = "Select Target File..."
        filename = ''
        while filename == '':
            filename = tkFileDialog.asksaveasfilename(title=title,
                                                      filetypes=filters,
                                                      initialdir=OUTPUT_PATH,
                                                      initialfile=OUTPUT_FILE)
        if filename is not None and filename != '':
            self.var_target.set(ntpath.basename(filename))
            self.parameters['target'] = filename

    def ok_quit(self):
        """Parses parameters to edit by reference to calling function/object."""
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        sep = '/' if '/' in cur_dir else '\\'
        self.parameters['modem'] = True if self.var_modem.get() else False
        if self.parameters['modem']:
            modem_file = cur_dir + sep + CORE_MODEM_FILE
            self.file_path_list.append(modem_file)
        self.parameters['lsf'] = True if self.var_lsf.get() else False
        if self.parameters['lsf']:
            lsf_file = cur_dir + sep + LSF_CORE_AGENTS_FILE
            self.file_path_list.append(lsf_file)
        self.parameters['meta'] = True if self.var_meta.get() else False
        for f in self.file_path_list:
            if not valid_path(f):
                if self.parameters['error'] is None:
                    self.parameters['error'] = []
                self.parameters['error'].append("ERROR: Invalid path {path}".format(path=f))
        self.parameters['files'] = self.file_path_list
        self.quit()


def clean_desc(desc):
    """
    Removes line feeds from description tag

    :param desc: (string) value from the Description tag to clean up
    :return: (string) cleaned up Description with no line feeds

    """
    return desc.replace('\n', ' ')


def valid_path(filename):
    """
    Validates a file path on local os or URL-based

    :param filename: (string) to be validated
    :return: {Boolean} result

    """
    if 'http://' in filename or 'https://' in filename:
        if 'http://' in filename:
            c = httplib.HTTPConnection(filename)
        else:
            c = httplib.HTTPSConnection(filename)
        c.request('HEAD', '')
        if c.getresponse().status == 200:
            return True
        else:
            return False
    if os.path.exists(filename):
        return True
    else:
        return False


def merge_mdf(files, target, meta=False):
    """
    Merges message definition files, sorted in ascending order of SIN.

    .. note::
       Potential issue with XML namespaces.

    :param files: (list of string) with each full path/filename to merge
    :param target: (string) target path/filename result of the merge
    :param meta: (Boolean) flag to use metadata tags in XML output of Service and Message
    :return: (string) error description if error, or None if successful

    """
    error_string = ''
    if files is None or len(files) < 2:
        error_string = "No files to merge."
    elif target is None:
        error_string = "No target file to output."
        # TODO: consider using the current active directory and a default filename "merged.idpmsg"
    else:
        base_filename, ext = os.path.splitext(target)
        if ext != '.idpmsg':
            target = target.replace(ext, '.idpmsg')
        if not valid_path(target.replace(os.path.basename(target), '')):
            return "ERROR: Invalid target file/path {target}".format(target=target)
        err_filename = base_filename + '_ERR.log'
        services = []
        exceptions = []
        root = ET.Element('MessageDefinition')
        root.tail = '\n'
        root.text = '\n  '
        trunk = ET.SubElement(parent=root, tag='Services')
        trunk.tail = '\n'
        trunk.text = '\n \t'
        tree = ET.ElementTree(root)
        for f in files:
            if not valid_path(f):
                exceptions.append("Source file/path %s does not exist" % f)
                break
            branch = ET.parse(f).getroot()
            '''
            # TODO: method for removing xml namespaces
            with open(f) as r:
                xmlstring = r.read()
            for key, value in NS.iteritems():
                xmlstring = xmlstring.replace(' xmlns:'+key+'=', '').replace('\"'+value+'\"', '')
                xmlstring = xmlstring.replace(key+':', '')
            branch = ET.fromstring(xmlstring)
            '''
            if branch.findall('Services'):
                for limb in branch[0]:
                    service = limb.find('SIN').text
                    if meta:
                        limb.set('sin', service)
                        limb.set('name', limb.find('Name').text)
                    for msg in limb.iter('Message'):
                        if meta:
                            msg.set('min', msg.find('MIN').text)
                            msg.set('name', msg.find('Name').text)
                    for desc in limb.iter('Description'):
                        desc.text = clean_desc(desc.text)
                    if service not in services:
                        services.append(service)
                        if limb.tail == '\n  ':
                            limb.tail = '\n    '
                        trunk.append(limb)
                    else:
                        exceptions.append("WARNING: Found duplicate SIN in \"{file}\" Services "
                                          "- ignoring SIN {sin}".format(file=f, sin=service))
            else:
                exceptions.append("WARNING: Invalid Message Definition File - no Services in {file}".format(file=f))
        if len(services) > 0:
            container = tree.find("Services")
            data = []
            for elem in container:
                key = elem.findtext("SIN")
                data.append((key, elem))
            data.sort()
            container[:] = [item[-1] for item in data]
            last_element_index = len(services) - 1
            trunk[last_element_index].tail = '\n  '
            for prefix, uri in NS.iteritems():
                # TODO: investigate why xsi is already in the namespace (had to comment out of NS above)
                root.set('xmlns:' + prefix, uri)
            tree.write(target, encoding='utf-8', xml_declaration=True)
        else:
            exceptions.append("ERROR: No Services found in source file set.")
        if len(exceptions) > 0:
            error_file = open(err_filename, 'w')
            for e in exceptions:
                if error_string != '':
                    error_string += '\n'
                error_string += e
            error_file.write(error_string)
            error_file.close()
    return error_string if error_string != '' else None


def _on_closing():
    """Graceful program exit if user closes the window."""
    sys.exit("Operation cancelled.")


def get_merge_parameters(files, target, modem, lsf, meta):
    """
    Displays a UI confirming merge setup and allowing modification.

    :param files: a list of file names to merge
    :param target: the target merged file name
    :param modem: (Boolean) to include core modem definitions
    :param lsf: (Boolean) to include SkyWave LSF Core+Agent Services
    :param meta: (Boolean) to include metadata tags in merged XML output
    :return: a dictionary consisting of

        * ``files`` - (list of string) file/path names to merge
        * ``target`` - (string) output file/path name
        * ``modem`` - (Boolean) flag to include core modem definitions
        * ``lsf`` - (Boolead) flag to include SkyWave LSF core/agent definitions
        * ``meta`` - (Boolean) flag to include XML tag metadata (Service and Message)
        * ``error`` - (None) if no errors or (list of string) any processing errors

    """
    error = None
    merge_parameters = {
        'files': files,
        'target': target,
        'modem': modem,
        'lsf': lsf,
        'meta': meta,
        'error': error
    }
    root = tk.Tk()
    dialog = MergeDialog(root, merge_parameters)
    root.protocol('WM_DELETE_WINDOW', _on_closing)
    root.mainloop()
    merge_parameters = dialog.parameters
    if len(merge_parameters['files']) < 2:
        err = "ERROR: Cannot merge fewer than 2 files."
        if merge_parameters['error'] is None:
            merge_parameters['error'] = [err]
        else:
            merge_parameters['error'].append(err)
    return merge_parameters


def parse_args(argv):
    """
    Parse the command line arguments.

    :param argv: An array containing the command line arguments
    :return: (dictionary) containing the command line arguments and their values

        * ``meta`` - (Boolean) flag to include metadata in XML tags for Service and Message
        * ``modem`` - (Boolean) flag to include core modem definitions
        * ``lsf`` - (Boolean) flag to include SkyWave LSF core/agent definitions
        * ``files`` - (list of string) input files to merge
        * ``target`` - (string) output file

    """
    global enable_smart_tags
    parser = argparse.ArgumentParser(description='Merge IDP Message Definition Files')
    parser.add_argument('-m', '--modem', required=False, dest='modem', action='store_true',
                        help=str("Import IDP Core Modem definitions."))
    parser.add_argument('-l', '--lsf', required=False, dest='lsf', action='store_true',
                        help=str("Import ORBCOMM/SkyWave LSF Core/Agent Service definitions."))
    parser.add_argument('-f', '--file', required=False, dest='files', action='append',
                        help=str("Source XML file (*.idpmsg) to merge. Accepts muliple entries. \n"
                                 " NOTE: use double-quoted path names."))
    parser.add_argument('-t', '--target', required=False, dest='target',
                        help=str("Destination XML file (*.idpmsg) to merge. \n"
                                 " NOTE: use double-quoted path name."))
    parser.add_argument('--meta', required=False, dest='meta', action='store_true',
                        help=str("Add metadata tags in XML attributes. NOTE: may not be supported by IDP gateway."))
    return vars(parser.parse_args(args=argv[1:]))


def main():
    user_options = parse_args(sys.argv)
    files = user_options['files']
    merge_parameters = get_merge_parameters(files=files,
                                            target=user_options['target'],
                                            modem=user_options['modem'],
                                            lsf=user_options['lsf'],
                                            meta=user_options['meta'])
    if merge_parameters['error'] is None:
        error = merge_mdf(files=merge_parameters['files'],
                          target=merge_parameters['target'],
                          meta=merge_parameters['meta'])
        if error is None:
            print("Operation completed.")
        else:
            print(error)
    else:
        for e in merge_parameters['error']:
            print(e)


if __name__ == "__main__":
    main()
