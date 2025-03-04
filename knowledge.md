# wrapper command

To work around the 30 second time limit imposed by the terminal command tool, you can use the `wrapper` command:

    wrapper run <command> [args]

If the wrapper command times out, the underlying command is still running and you can continue viewing its live output
with `wrapper reattach`. If you need to kill the underlying command, use `wrapper kill`.
