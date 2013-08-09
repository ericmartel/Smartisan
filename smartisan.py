# Written by Eric Martel (emartel@gmail.com / www.ericmartel.com)
# this plugin is meant to help automate calls to artisan for Laravel 4 from Sublime Text

# All of Smartisan Plugin is licensed under the MIT license.
# Copyright (c) 2013 Eric Martel <emartel@gmail.com>
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sublime
import sublime_plugin

import subprocess
import webbrowser
import threading
import os
import json

porting_layer = None;

class Python2Layer():
    def __init__(self):
        self.version = (2,6)

    def create_subprocess(self, in_command, in_from):
        p = subprocess.Popen(in_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=in_from, shell=True)
        result, err = p.communicate();
        return result, err;

class Python3Layer():
    def __init__(self):
        self.version = (3,0);

    def create_subprocess(self, in_command, in_from):
        p = subprocess.Popen(in_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=in_from, shell=True)
        result, err = p.communicate();
        result = result.decode("utf-8");
        err = err.decode("utf-8");
        return result, err;

import sys
try:
    if sys.version_info.major == 3:
        porting_layer = Python3Layer();
    else:
        porting_layer = Python2Layer();
except AttributeError:
    porting_layer = Python2Layer();

# Taken from http://stackoverflow.coexm/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def is_environment_ok():
    php_executable = "php.exe";
    if(sublime.platform() != "windows"):
        php_executable = "php"
    if which(php_executable) == None:
        smartisan.display_error("php is not found on your environment.  It is required to execute artisan commands.  Consider adding it to the PATH environment variable");
        return False;
    return True;

# todo: check for better solution
def ConstructCommand(in_command):
    command = ''
    if(sublime.platform() == "osx"):
        command = 'source ~/.bash_profile && '
    command += in_command
    return command

def ExecuteCommand(in_command, in_from = ''):
    command = ConstructCommand(in_command);
    result, err = porting_layer.create_subprocess(command, in_from);
    return result, err;

class Artisan():
    def __init__(self, in_artisan_path, in_path):
        self.artisan_path = in_artisan_path;
        self.path = in_path;
        self.version = "";
        self.sections = [];

class Module():
    def __init__(self, in_name):
        self.name = in_name;
        self.commands = [];

class Command():
    def __init__(self, in_name, in_command, in_description):
        self.name = in_name;
        self.command = in_command;
        self.description = in_description;

class Smartisan():

    def log_line(self, in_line, in_prefix = ""):
        import datetime
        import time
        ts = time.time()
        when = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        lines = in_line.split('\n');
        for l in lines:
            if len(l.strip()) > 0:
                print("Smartisan%(prefix)s [%(when)s]: %(line)s" % {"when": when, "line": l, "prefix": in_prefix});

    def display_status(self, in_status):
        sublime.status_message("Smartisan: " + in_status);

    def display_warning(self, in_warning):
        self.log_line(in_warning, " WARNING");
        sublime.message_dialog(in_warning);

    def display_error(self, in_error):
        self.log_line(in_error, " ERROR");
        sublime.error_message(in_error);

smartisan = Smartisan();

class SmartisanFolderIndexer(threading.Thread):
    def __init__(self, in_folder):
        self.folder = in_folder;
        self.found_files = [];
        threading.Thread.__init__(self);

    def run(self):
        # From here, add all the folders that can be found
        # For each of these folders, scan for a file called 'artisan'
        smartisan.log_line("Indexing " + self.folder);
        
        for root, subfolders, files in os.walk(self.folder):
            for file in files:
                if(file == "artisan"):
                    completeFile = os.path.join(root, file);
                    smartisan.log_line("Found at " + completeFile);
                    self.found_files.append(Artisan(completeFile, root + os.sep));

class SmartisanData():
    def __init__(self):
        self.artisan_files = [];

    def find_artisan(self, in_folder):
        folder_sections = in_folder.split(os.sep);
        included_sections = len(folder_sections);
        while(included_sections > 0):
            recreated_folder = os.sep.join(folder_sections[0:included_sections]) + os.sep;
            artisan_file = recreated_folder + "artisan";
            if(os.path.exists(artisan_file)):
                artisan = Artisan(artisan_file, recreated_folder)
                self.process_artisan(artisan);
                return artisan;
            included_sections = included_sections - 1;
        return None;

    def index_folders(self, in_folders):
        smartisan.display_status("Indexing Folders");

        indexingThreads = [];
        for folder in in_folders:
            t = SmartisanFolderIndexer(folder);
            indexingThreads.append(t);

        for t in indexingThreads:
            t.start();

        for t in indexingThreads:
            t.join();

        # clean up old data
        # if the artisan file cannot be found anymore, remove it
        self.artisan_files[:] = [tup for tup in self.artisan_files if(self.artisan_still_exists(tup))];

        # add the new artisan files to the dictionary
        for t in indexingThreads:
            for f in t.found_files:
                self.process_artisan(f);

        sublime.set_timeout(self.status_num_artisan, 0);

    def artisan_still_exists(self, artisan_parts):
        return os.path.exists(artisan_parts.artisan_path);

    def extract_module_commands(self, lines, start, name):
        commands = [];

        linenum = start;
        while(lines[linenum].startswith("  ") == True and linenum < len(lines)):
            line_parts = lines[linenum].split();
            command_name = line_parts[0];
            command_command = command_name;
            if(command_name.startswith(name + ":")):
                command_name = command_name[len(name) + 1:];
            description = " ".join(line_parts[1:]);
            command = Command(command_name, command_command, description);
            commands.append(command);
            linenum = linenum + 1;

        return commands;

    def process_artisan(self, artisan_parts):
        if(not os.path.exists(artisan_parts.artisan_path)):
            return;

        result, err = ExecuteCommand("php artisan -list", artisan_parts.path);

        if(len(err)):
            smartisan.display_error("Cannot process artisan:\n" + err);
            return;

        # parse the results
        lines = str.split(result, '\n');

        artisan_parts.version = lines[0].strip();

        linenum = 1;
                
        while lines[linenum].startswith("Available commands:") == False and linenum < len(lines):
            linenum = linenum + 1;

        if(linenum == len(lines)):
            smartisan.display_error("Cannot parse artisan output");
            return;
        
        artisan_parts.modules = [];

        artisan_module = Module('artisan');
        linenum = linenum + 1; # Skip available commands

        current_module = artisan_module;

        while(linenum < len(lines)):
            commands = self.extract_module_commands(lines, linenum, current_module.name);
            current_module.commands = commands;
            artisan_parts.modules.append(current_module);
            # see if there's a new module to read
            linenum = linenum + len(commands);
            if(linenum < len(lines)):
                current_module = Module(lines[linenum]);
                linenum = linenum + 1;
        
        self.artisan_files.append(artisan_parts);

    def status_num_artisan(self):
        smartisan.display_status("%d artisan files indexed" % len(self.artisan_files));

smartisanData = SmartisanData();

class SmartisanIndexFoldersCommand(sublime_plugin.WindowCommand):
    def run(self):
        if(len(self.window.folders()) == 0):
            smartisan.display_warning("No Folders open");

        smartisanData.index_folders(self.window.folders());

class SmartisanListIndexedArtisanCommand(sublime_plugin.WindowCommand):
    def description(self):
        return "Lists all Indexed Artisan files";

    def run(self):
        if(len(smartisanData.artisan_files) == 0):
            smartisan.display_warning("No Known Artisan");

        artisan_list = [];

        for a in smartisanData.artisan_files:
            artisan_entry = [a.version, a.path];
            artisan_list.append(artisan_entry);

        self.window.show_quick_panel(artisan_list, self.on_done)

    def on_done(self, picked):
        if picked == -1:
            return

class BaseArtisanCommand(sublime_plugin.WindowCommand):
    artisan = None;

    def is_enabled(self):
        valid_view = self.window.active_view() != None and len(self.window.active_view().file_name()) > 0;
        return is_environment_ok() and valid_view;
    def is_visible(self):
        return is_environment_ok();

    def get_artisan_for_view(self):
        folder_name, filename = os.path.split(self.window.active_view().file_name());
        folder_name += os.sep;
        for a in smartisanData.artisan_files:
            if folder_name.startswith(a.path):
                return a;
        # nothing found, try to see if a parent contains an artisan file
        smartisan.log_line("View '%(filename)s' didn't match a known artisan file, trying to find one" % {"filename":filename});
        artisan = smartisanData.find_artisan(folder_name);
        if(artisan):
            smartisan.log_line("Found artisan file at '%(path)s'" % {"path": artisan.path});
        else:
            smartisan.log_line("No artisan found");
        return artisan;

    def set_working_artisan(self, in_artisan):
        self.artisan = in_artisan;

    def get_modules(self):
        if self.artisan == None:
            return None;

        modules = [];

        for m in self.artisan.modules:
            description = "Contains: ";
            for c in m.commands:
                description = description + c.name + ", ";
            if(len(m.commands) > 0):
                description = description[0:len(description) - 2];
            module_entry = [m.name, description];
            modules.append(module_entry);

        return modules;

    def get_commands(self, picked):
        if self.artisan == None:
            return None;

        self.selected_module = self.artisan.modules[picked];

        commands = [];

        for c in self.selected_module.commands:
            command_entry = [c.name, c.description];
            commands.append(command_entry);

        return commands;

    def extract_module_command_names(self, line):
        line_parts = line.split();
        if(len(line_parts) == 0):
            return None, None;

        module_and_command = line_parts[0];
        elements = module_and_command.split(':');

        if(len(elements) == 1):
            # no : was found, so it's in the default namespace / module, in this plugin, we're calling it artisan
            elements.append(elements[0]);
            elements[0] = "artisan";
        else:
            if(len(elements) > 2):
                smartisan.display_warning("Strangely, we found more than 1 ':' in the command!");

        return elements[0], elements[1];


    def identify_module(self, module):
        self.selected_module = None;
        self.extracted_module = "empty";

        if(self.artisan == None):
            smartisan.display_error("No artisan file selected");
            return;

        line_parts = module.split();
        if(len(line_parts) == 0):
            smartisan.display_error("Cannot identify module, no line specified");
            return;

        module, command = self.extract_module_command_names(line_parts[0]);

        for m in self.artisan.modules:
            if m.name == module:
                self.selected_module = m;
                self.extracted_module = module;
                return;

    def identify_command(self, command):
        self.selected_command = None;
        self.extracted_command = "empty";

        if(self.selected_module == None):
            smartisan.display_error("No module selected");
            return;

        line_parts = command.split();
        if(len(line_parts) == 0):
            smartisan.display_error("Cannot identify command, no line specified");
            return;

        module, command = self.extract_module_command_names(line_parts[0]);

        if(module != self.selected_module.name):
            smartisan.display_error("Module name mismatch!");
            return;

        for c in self.selected_module.commands:
            if c.name == command:
                self.selected_command = c;
                self.extracted_module = command;
                return;

    def execute_command(self, input):
        execution_string = "php artisan %(command)s %(arguments)s" % {"command": self.selected_command.command, "arguments": input};
        smartisan.log_line("executing: " + execution_string);
        result, err = ExecuteCommand(execution_string, self.artisan.path);

        if(len(err)):
            smartisan.display_error("Smartisan execution error:\n" + err);
        else:
            smartisan.log_line(result);

    def get_arguments(self):
        caption = "Arguments for %(module)s:%(command)s:" % {"module": self.selected_module.name, "command": self.selected_command.name};

        #fetch the arguments
        self.window.show_input_panel(caption, '', self.on_arguments_done, self.on_arguments_change, self.on_arguments_cancel);

    def on_arguments_done(self, input):
        # execute the command
        if(self.validate_command(input)):
            self.execute_command(input);

    def on_arguments_change(self, input):
        pass

    def on_arguments_cancel(self):
        pass

    def validate_command(self, input):        
        if(self.selected_module == None):
            smartisan.display_error("The module '%(module)s' is not available from your artisan located at '%(path)s'" % {"module": self.extracted_module, "path": self.artisan.path});
            return False;

        if(self.selected_command == None):
            smartisan.display_error("The command '%(command)s' could not be found in module '%(module)s' of your artisan located at '%(path)s'" % {"command": self.extracted_command, "module": self.selected_module.name, "path": self.artisan.path});
            return False;
        return True;

class SmartisanSelectCommand(BaseArtisanCommand):
    def run(self):
        artisan = self.get_artisan_for_view();

        if(artisan == None):
            smartisan.display_error("No Artisan found for current file");
            return;

        self.set_working_artisan(artisan);

        available_modules = self.get_modules();
        self.window.show_quick_panel(available_modules, self.on_selected_module)

    def on_selected_module(self, picked):
        if picked == -1:
            return

        # can't reuse the quick panel right away, sleep and launch it
        self.available_commands = self.get_commands(picked);
        sublime.set_timeout(self.show_commands_quick_panel, 10);

    def show_commands_quick_panel(self):
        self.window.show_quick_panel(self.available_commands, self.on_selected_command);

    def on_selected_command(self, picked):
        if picked == -1:
            return

        self.selected_command = self.selected_module.commands[picked];
        self.get_arguments();


class SmartisanRunCommand(BaseArtisanCommand):
    def run(self, **args):
        artisan = self.get_artisan_for_view();

        if(artisan == None):
            smartisan.display_error("No Artisan found for current file");
            return;

        self.set_working_artisan(artisan);
        
        command = self.get_command(args);
        if(command == None):
            smartisan.display_error("Failed to provide a command to run");
            return;

        self.construct_command(command);
        if('with_input' in args and args['with_input'].lower() != "false"):
            self.get_arguments();
        else:
            self.execute_command("");

    def get_command(self, args):
        if('command' in args):
            return args['command'];

        return None;

    def construct_command(self, command):
        self.identify_module(command);
        if(self.selected_module == None):
            smartisan.display_error("The module '%(module)s' is not available from your artisan located at '%(path)s'" % {"module": self.extracted_module, "path": self.artisan.path});
            return;
        self.identify_command(command);
        if(self.selected_command == None):
            smartisan.display_error("The command '%(command)s' could not be found in module '%(module)s' of your artisan located at '%(path)s'" % {"command": self.extracted_command, "module": self.selected_module.name, "path": self.artisan.path});
            return;