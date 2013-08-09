# Smartisan Plugin for Sublime Text

This plugin aims at making it easier for users of the `Laravel 4` framework to interface with their `artisan` `CLI`.

## Install

The preferred method is to use the [Sublime Package Manager](http://wbond.net/sublime_packages/package_control) (soon). Alternatively, the files can be obtained on github:

    $ https://github.com/ericmartel/Smartisan

## Documentation

Still work in progress:

`smartisan_select` or `Smartisan: Select Command` from the command palette will open a palette dropdown with a list of "namespaces / modules" in artisan, and once you select it, it changes to all the available commands.  Then, an input is prompted if you want to supply additional parameters

`smartisan_run` (which should be used more as a key binding command) checks 2 arguments: `command` which is the command to execute, and `with_input` set to anything different than `"false"` will prompt with an input field before executing the command.  This way you could do something like:

    {
        "keys": ["super+shift+k"], "command": "smartisan_run", "args": {"command": "key:generate", "with_input": "False"},
    }


# License

All of Smartisan Plugin for Sublime Text is licensed under the MIT license.

Copyright (c) 2013 Eric Martel <emartel@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
