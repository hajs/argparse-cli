This module requires argparse which is part of Python 2.7 and is available separately for older Python versions.

It automatically generates command line parsers from a class definition. This may not work for complex command line interfaces but gets the job done for common use cases.

Methods prefixed with `do_` are translated into sub-commands, parameters without default value become positional arguments and parameters with default-values become optional parameters. Doc-strings are used for help texts. Additional help can be put in help-keyword-parameters. Global options can be specified with the setup-method.

Here is an example:

```
from argparse_cli import Cli

class Daemon(Cli):
    "this is an example daemon"
    
    def setup(self, pidfile="~/.daemon.pid"): 
        self.pidfile = pidfile

    def do_start(self, document_root): 
        "start daemon"
    
    def do_stop(self, force=False, help={"force":"force stop"}): 
        "stop daemon"
        os.kill(int(open(self.pidfile).read()))

if __name__ == "__main__":
    cli = Daemon()
    cli.run()
```



Calling the module without arguments:
<blockquote>
<pre>
# python demo.py<br>
usage: demo.py [-h] [--pidfile [PIDFILE]] {start,stop} ...<br>
demo.py: error: too few arguments`<br>
</pre>
</blockquote>

Let's see the generated help:
<blockquote>
<pre>
# python demo.py --help<br>
usage: demo.py [-h] [--pidfile [PIDFILE]] {start,stop} ...<br>
this is an example daemon<br>
positional arguments:<br>
{start,stop}         sub-command help<br>
start              start daemon<br>
stop               stop daemon<br>
optional arguments:<br>
-h, --help           show this help message and exit<br>
--pidfile [PIDFILE]  default: '~/.daemon.pid'<br>
</pre>
</blockquote>

Help for the start command:
<blockquote>
<pre>
# python demo.py start --help<br>
usage: demo.py start [-h] [document_root]<br>
<br>
positional arguments:<br>
document_root<br>
<br>
optional arguments:<br>
-h, --help     show this help message and exit<br>
</pre>
</blockquote>

Help for the stop command:
<blockquote>
<pre>
# python demo.py stop --help<br>
usage: demo.py [-h] [--pidfile [PIDFILE]] {start,stop} ...<br>
<br>
this is an example daemon<br>
<br>
positional arguments:<br>
{start,stop}         sub-command help<br>
start              start daemon<br>
stop               stop daemon<br>
<br>
optional arguments:<br>
-h, --help           show this help message and exit<br>
--pidfile [PIDFILE]  default: '~/.daemon.pid'<br>
</pre>
</blockquote>