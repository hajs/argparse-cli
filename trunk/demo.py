from argparse_cli import Cli

class Daemon(Cli):
    "this is an example daemon"
    
    def setup(self, pidfile="~/.daemon.pid"): 
        self.pidfile = pidfile

    def do_start(self, document_root): 
        "start daemon"
    
    def do_stop(self, force=False, help={"force":"force stop"}): 
        "stop daemon"

if __name__ == "__main__":
    cli = Daemon()
    cli.run()
