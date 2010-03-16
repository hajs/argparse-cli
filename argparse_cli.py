# -*- coding: utf-8 -*-
# TODO
#  * argument groups (for non mutually exclusive arguments)
#  * sub-sub-commands?
#  * print_usage/print_help
#  * support argument defaults from environment variables
#  * support argument defaults from configuration files
import sys
import os
import __main__
import inspect
import argparse



def inspect_func(func, remove_self=True):
    names, var_args_name, var_kw_name, default_vals = inspect.getargspec(func)
    default_vals = default_vals or ()
    defaults = dict(zip(names[-len(default_vals):], default_vals))

    if names and remove_self and names[0] == "self":
        del names[0]

    default_count = len(default_vals)
    if default_count:
        required_args = names[:-default_count]
    else:
        required_args = names
    return names, defaults, required_args, var_args_name



def dapply(func, func_args, func_kwargs):
    kwargs = dict(func_kwargs) # work on copy
    names, defaults, required_args, var_args_name = inspect_func(func)
    
    call_args = []
    call_kwargs = {}

    i = -1
    for arg_name in names:
        if arg_name in kwargs:
            call_args.append(func_kwargs.pop(arg_name))
        else:
            if i + 1 < len(func_args):
                i += 1
                call_args.append(func_args[i])
            else:
                call_kwargs[arg_name] = defaults.get(arg_name)

    if var_args_name:
        try:
            call_args.extend(func_kwargs.pop(var_args_name))
        except KeyError:
            call_args.extend(func_args[i:])

    return func(*call_args, **call_kwargs)




def boolean(s):
    s = s.strip().lower()
    if s and s in ("1", "true", "yes", "on"):
        return True
    elif s and s in ("0", "false", "no", "off"):
        return False
    else:
        raise ValueError, "invalid boolean value %r" % s



class Cli(object):
    
    type2validator = {
       bool: boolean,
       None: lambda x:x
    }
    long_prefix = "--"


    def __init__(self):
        self.parser = self._create_arg_parser()
        self._populate_parser()
        
        
    def _populate_parser(self):
        setup = getattr(self, "setup", None)
        if setup:
            self.setup_options, self.setup_args = self._add_func_parser(self.parser, setup)
        else:
            self.setup = None

        cmd = self._discover_commands()
        if cmd:
            self.subparsers = self.parser.add_subparsers(help="sub-command help")
            for name, func in cmd.items():
                parser = self.subparsers.add_parser(name, help=self._get_help(func))
                parser.set_defaults(_func=func)
                self._add_func_parser(parser, func)


    def _create_arg_parser(self):
        version = getattr(self, "version", None) or getattr(__main__, "__version__", None)
        desc = self._get_help(self) or self._get_help(__main__)
        return argparse.ArgumentParser(description=desc, version=version)


    def _add_func_parser(self, parser, func):
        
        def _validator(name, value=None):
            def decorator(v):
                def wrapper(s):
                    return v(s)
                return wrapper
            validate = ap_types.get(name, None)
            if not validate:
                    validate = getattr(self, "validate_%s_%s" % (fname, name), None)
            else:
                validate = None
            if not validate:
                validate = getattr(self, "validate_%s" % name, None)
            if not validate:
                value_type = type(value)
                validate = self.type2validator.get(value_type, None)
            if not validate:
                validate = self.type2validator.get(None)
            v = decorator(validate)
            v.__name__ = name
            return v

        def _add_required(p, name, value):
            try:
                option_help = help_dict[name]
            except KeyError, e:
                option_help = "default: %(default)r"
            if callable(value):
                validate = value
                value = None
            else:
                validate = _validator(name, value)
            p.add_argument(
               self._format_option(name), 
               help=option_help,
               type=validate,
               default=value,
               dest=name,
               nargs=ap_nargs.get(name, "?"))
    
        fname = func.__name__
        if fname.startswith("do_"):
            fname = fname[3:]

        names, defaults, required_args, var_args_name = inspect_func(func)

        help_dict = defaults.pop("help", {})
        help_dict.update(defaults.pop("_help", {}))
        ap_types = defaults.pop("_types", {})
        ap_nargs = defaults.pop("_nargs", {})
        ap_mutex = defaults.pop("_mutex", [])
        
        for args in ap_mutex:
            group = parser.add_mutually_exclusive_group(required=True)
            gdefs = {}
            for a in args:
                value = defaults.pop(a)
                _add_required(group, a, value)
                gdefs[a] = value
            #group.set_defaults(**gdefs)
        for name, value in defaults.items():
            if name.startswith("_"):
                continue
            _add_required(parser, name, value)
    
        for a in required_args:
            if a.startswith("_"):
                continue
            parser.add_argument(
               a,  help=help_dict.get(a, None),
               type=_validator(a),
               nargs=ap_nargs.get(a, "?"))
            
        if var_args_name:
            parser.add_argument(var_args_name,
               help=help_dict.get(var_args_name, None),
               nargs=ap_nargs.get(var_args_name, "*"))
            parser.set_defaults(_var_args=var_args_name)

        return defaults, required_args


    def _format_option(self, name):
        return "%s%s" % (self.long_prefix, name.replace("_", "-"))


    def _get_help(self, obj):
        try:
            return getattr(obj, "__help__")
        except AttributeError, e:
            return getattr(obj, "__doc__", "")


    def _discover_commands(self):
        cmd = {}
        for name in dir(self):
            if name.startswith("do_"):
                cmd[name[3:].replace("_", "-")] = getattr(self, name)
        return cmd


    def run(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        if self.setup and "_unknown" in self.setup_args:
            args_namespace, unknown = self.parser.parse_known_args(argv)
            args_namespace._unknown = unknown
            self.setup_args.remove("_unknown")
        else:
            args_namespace = self.parser.parse_args(argv)
        args = dict(args_namespace.__dict__)

        if self.setup:
            setup_kwargs = {}
            for name, default_value in self.setup_options.items():
                setup_kwargs[name] = args.get(name, default_value)
            for name in self.setup_args:
                setup_kwargs[name] = args.pop(name)
            dapply(self.setup, (), setup_kwargs)

        var_args = args.pop("_var_args", None)
        if var_args:
            var_args = args.pop(var_args, ())
        else:
            var_args = ()
        func = args.pop("_func")
        return dapply(func, var_args, args)



        
class TestCli(Cli):
    """
    This is a simple test command line interface class

    Let's see how it works
    
    
    >>> t = TestCli()
    >>> t.run(["--init-value=foobar", "test-nop"])
    >>> t.init
    'foobar'
    
    >>> t.run(["test-bool", "--flag=yes"])
    True
    
    >>> t.run(["test-varargs"])
    ()
    
    >>> t.run(["test-varargs", "fn.ext"])
    ('fn.ext',)
    
    >>> t.run(["test-varargs2", "foo"])
    ('foo',)

    >>> t.run(["test-exists", "/etc//passwd"])
    /etc/passwd exists

    >>> t.run(["test-mutually-exclusive", "--foo=1"])
    (True, False)

    """
    version = "0.1"


    def setup(self, init_value="", verbose=True):
        self.init = init_value
        
    def do_test_nop(self, foo="bar"):
        "this sub-command does nothing"
    
    def do_test_bool(self, flag=False):
        print flag

    def do_test_varargs(self, *files):
        print files

    def do_test_varargs2(self, _nargs={"files":"+"}, *files):
        print files

    def do_test_exists(self, filename):
        print filename, "exists"
        
    def validate_filename(self, filename):
        filename = os.path.normpath(filename)
        if not os.path.exists(filename):
            raise ValueError("%r does not exist" % filename)
        return filename

    def do_test_mutually_exclusive(self, foo=False, bar=False, _mutex=[("foo", "bar")]):
        print (foo, bar)




if __name__ == "__main__":    
    import doctest
    doctest.testmod()
