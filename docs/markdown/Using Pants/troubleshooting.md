---
title: "Troubleshooting / common issues"
slug: "troubleshooting"
excerpt: "Frequently asked questions (FAQs) and known issues you may encounter."
hidden: false
createdAt: "2020-04-10T19:42:28.637Z"
updatedAt: "2022-05-25T14:34:36.454Z"
---
> 👍 We love giving help!
> 
> See [Getting Help](doc:getting-help). We would love to help!
> 
> If you are confused by something, likely someone else will run into the same issue. It is helpful for us to know what is going wrong so that we can improve Pants and improve this documentation.

Debug tip: enable stack traces and increase logging
---------------------------------------------------

Pants defaults to not displaying the full stack trace when it encounters an error. Pants also defaults to logging at the info level.

When you encounter an exception, it can help to use the global options `--print-stacktrace` and `-ldebug`, like this:

```bash
./pants --print-stacktrace -ldebug <rest of your command>
```

Setting the option `--pex-verbosity=9` can help debug exceptions that occur when building .pex files.

Once you have this stack trace, we recommend copying it into Pastebin or a GitHub Gist, then opening a GitHub issue or posting on Slack. Someone from the Pants team would be happy to help. See [Getting Help](doc:getting-help).

Debug tip: inspect the sandbox with `--keep-sandboxes`
----------------------------------------------------------

Pants runs most processes in a hermetic sandbox (temporary directory), which allows for safely caching and running multiple processes in parallel. 

Use the option `--keep-sandboxes=always` for Pants to log the paths to these sandboxes, and to keep them around after the run. You can then inspect them to check if the files you are expecting are present.

```bash
./pants --keep-sandboxes=always lint src/project/app.py
...
21:26:13.55 [INFO] preserving local process execution dir `"/private/var/folders/hm/qjjq4w3n0fsb07kp5bxbn8rw0000gn/T/process-executionQgIOjb"` for "Run isort on 1 file."
...
```

You can also pass `--keep-sandboxes=on_failure`, to preserve only the sandboxes of failing processes.

There is even a `__run.sh` script in the directory that will run the process using the same argv and environment that Pants would use.

Cache or pantsd invalidation issues
-----------------------------------

If you are using the latest stable version of Pants and still experience a cache invalidation issue: we are sorry for the trouble. We have not yet added a comprehensive goal to "clear all caches", because we are very interested in coming up with coherent solutions to potential issues (see  for more information). If you experience a cache issue, please absolutely [file a bug](https://github.com/pantsbuild/pants/issues/new) before proceeding to the following steps.

To start with, first try using `--no-pantsd`. If that doesn't work, you can also try `--no-local-cache`.

If `--no-pantsd` worked, you can restart `pantsd`, either by:

- Killing the `pantsd` process associated with your workspace. You can use `ps aux | grep pants` to find the PID, the `kill -9 <pid>`. 
- Deleting the `<build root>/.pids` directory. 

If this resolves the issue, please report that on the ticket and attach the recent content of the `.pants.d/pantsd/pantsd.log` file.

If restarting `pantsd` is not sufficient, you can also use `--no-local-cache` to ignore the persistent caches. If this resolves the issue, then it is possible that the contents of the cache (at `~/.cache/pants`) will be useful for debugging the ticket that you filed: please try to preserve the cache contents until it can be resolved.

Pants cannot find a file in your project
----------------------------------------

Pants may complain that it cannot find a file or directory, even though the file does indeed exist.

This error generally happens because of the option `pants_ignore` in the `[GLOBAL]` scope, but you should also check for case-mismatches in filenames ("3rdparty" vs "3rdParty"). By default, Pants will read your top-level `.gitignore` file to populate `pants_ignore`, along with ignoring `dist/` and any top-level files/directories starting with `.`.

To override something included in your `.gitignore`, add a new value to `pants_ignore` and prefix it with `!`, like the below. `pants_ignore` uses the [same syntax as gitignore](https://git-scm.com/docs/gitignore).

```toml pants.toml
[GLOBAL]
pants_ignore.add = ["!folder/"]
```

Alternatively, you can stop populating `pants_ignore` from your `.gitignore` by setting `pants_ignore_use_gitignore = false` in the `[GLOBAL]` scope.

Import errors and missing dependencies
--------------------------------------

Because Pants runs processes in hermetic sandboxes (temporary directories), Pants must properly know about your [dependencies](doc:targets#dependencies-and-dependency-inference) to avoid import errors. 

Usually, you do not need to tell Pants about your dependencies thanks to dependency inference, but sometimes dependency inference is not set up properly or cannot work.

To see what dependencies Pants knows about, run `./pants dependencies path/to/file.ext` and `./pants dependencies --transitive`.

Is the missing import from a third-party dependency? Common issues:

- Pants does know about your third-party requirements, e.g. missing `python_requirements` and `go_mod` target generators.
  - To see all third-party requirement targets Pants knows, run `./pants --filter-target-type=$tgt list ::`, where Python: `python_requirement`, Go: `go_third_party_package`, and JVM: `jvm_artifact`.
  - Run `./pants tailor ::`, or manually add the relevant targets.
- The dependency is missing from your third-party requirements list, e.g. `go.mod` or `requirements.txt`.
- The dependency exposes a module different than the default Pants uses, e.g. Python's `ansicolors` exposing `colors`.
  - [Python](doc:python-third-party-dependencies): set the `modules` field and `module_mapping` fields.
  - [JVM](doc:reference-jvm-artifact): set the `packages` field on `jvm_artifact` targets.
- Python: check for any [undeclared transitive dependencies](doc:python-third-party-dependencies#advanced-usage).

Is the missing import from first-party code? Common issues:

- The file does not exist.
  - Or, it's ignored by Pants. See the above guide "Pants cannot find a file in your project".
- The file is missing an owning target like `python_sources`, `go_package`, or `resources`.
  - Run `./pants list path/to/file.ext` to see all owning targets.
  - Try running `./pants tailor ::`. Warning: some target types like [`resources` and `files`](doc:assets) must be manually added.
- [Source roots](doc:source-roots) are not set up properly (Python and JVM only).
  - This allows converting file paths like `src/py/project/app.py` to the Python module `project.app`.

 Common issues with both first and third-party imports:

- Ambiguity. >1 target exposes the same module/package.
  - If it's a third-party dependency, you should likely use multiple "resolves" (lockfiles). Each resolve should have no more than one of the same requirement.  See [Python](doc:python-third-party-resolves#multiple-lockfiles) and [JVM](doc:jvm-overview).
  - If it's a first-party dependency, you may have unintentionally created multiple targets owning the same file. Run `./pants list path/to/file.ext` to see all owners. This often happens from overlapping `sources` fields. If this was intentional, follow the instructions in the ambiguity warning to disambiguate via the `dependencies` field.
- Some target types like `resources` and `files` often need to be explicitly added to the `dependencies` field and cannot be inferred (yet).
- Multiple resolves (Python and JVM).
  - A target can only depend on targets that share the same "resolve" (lockfile).
  - Pants will warn when it detects that the import exists in another resolve. This usually implies you should either change the current target's `resolve` field, or use the `parametrize()` mechanism so that the code works with multiple resolves.
  - See [Python](doc:python-third-party-resolves#multiple-lockfiles) and [JVM](doc:jvm-overview).

When debugging dependency inference, it can help to explicitly add the problematic dependency to the `dependencies` field to see if it gets the code running. If so, you can then try to figure out why dependency inference is not working.

"Out of space" error: set an alternative tmpdir
-----------------------------------------------

It may be necessary to explicitly set the directory Pants uses as a temporary directory. For example, if the system default temporary directory is a small partition, you may exhaust that temp space.

Use the global option `local_execution_root_dir` to change the tmpdir used by Pants.

```toml pants.toml
[GLOBAL]
local_execution_root_dir = "/mnt/large-partition/tmpdir"
```

"No space left on device" error while watching files
----------------------------------------------------

On Linux, Pants uses `inotify` to watch all files and directories related to any particular build. Some systems have limits configured for the maximum number of files watched. To adjust the limit on file watches, you can run:

```shell
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

How to change your cache directory
----------------------------------

You may change any of these options in the `[GLOBAL]` section of your `pants.toml`:

[block:parameters]
{
  "data": {
    "h-0": "Option",
    "h-1": "What it does",
    "h-2": "Default",
    "0-0": "`local_store_dir`",
    "0-1": "Stores the results of running subprocesses and of some file operations.",
    "0-2": "`~/.cache/pants/lmdb_store`",
    "1-0": "`named_caches_dir`",
    "1-1": "Stores the caches for certain tools used by Pants, like PEX's cache for resolving Python requirements.",
    "1-2": "`~/.cache/pants/named_caches`",
    "2-0": "`pants_workdir`",
    "2-1": "Stores some project-specific logs; used as a temporary directory when running `./pants repl` and `./pants run`.  \n  \nThis is not used for caching.  \n  \nThis must be relative to the build root.",
    "2-2": "`<build_root>/.pants.d/`",
    "3-0": "`pants_distdir`",
    "3-1": "Where Pants writes artifacts to, such as the result of `./pants package`.  \n  \nThis is not used for caching; you can delete this folder and still leverage the cache from `local_store_dir`.  \n  \nThis must be relative to the build root.",
    "3-2": "`<build_root>/dist/`"
  },
  "cols": 3,
  "rows": 4,
  "align": [
    "left",
    "left",
    "left"
  ]
}
[/block]

For `local_store_dir` and `named_caches_dir`, you may either specify an absolute path or a relative path, which will be relative to the build root. You may use the special string `%(homedir)s` to get the value of `~`, e.g. `local_store_dir = "%(homedir)s/.custom_cache/pants/lmdb_store"`.

It is safe to delete these folders to free up space.

You can also change the cache used by the `./pants` script described in [Installing Pants](doc:installation), which defaults to `~/.pants/cache/setup`. Either set the environment variable `PANTS_SETUP_CACHE` or change the Bash script directly where it defines `PANTS_SETUP_CACHE`. You may use an absolute path or a path relative to the build root. 

BadZipFile error when processing Python wheels
----------------------------------------------

This can happen if your temporary directory (`/tmp/` by default) is not on the same filesystem as `~/.cache/pants/named_caches`, and is caused by the fact that `pip` is not concurrency-safe when moving files across filesystems.

The solution is to move `~/.cache/pants`, or at least the `named_caches_dir`(see [above](#how-to-change-your-cache-directory)), to the same filesystem as the temporary directory, or vice versa.

"Double requirement given" error when resolving Python requirements
-------------------------------------------------------------------

This is an error from `pip`, and it means that the same 3rd-party Python requirement—with different version constraints—appears in your dependencies.

You can use `./pants peek` to help identify why the same requirement is being used more than once:

```shell Shell
# Check the `requirements` key to see if it has the problematic requirement.
./pants --filter-target-type=python_requirement peek ::
```

macOS users: issues with system Python interpreters
---------------------------------------------------

The macOS system Python interpreters are broken in several ways, such as sometimes resulting in:

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: '/Library/Python/3.7'
```

You can set the option `interpreter_search_paths` in the `[python]` scope to teach Pants to ignore the interpreters in `/usr/bin`. See [here](doc:python-interpreter-compatibility#changing-the-interpreter-search-path) for more information.

"Too many open files" error
---------------------------

You may encounter this error when running Pants:

```
./pants count-loc helloworld/greet/f.py

ERROR: Could not initialize store for process cache: "Error making env for store at \"/Users/pantsbuild/.cache/pants/lmdb_store/processes/2\": Too many open files"

(Use --print-exception-stacktrace to see more error details.)
```

This sometimes happens because Pants uses lots of file handles to read and write to its cache at `~/.cache/pants/lmdb_store`; often, this is more than your system's default.

This can be fixed by setting `ulimit -n 10000`. (10,000 should work in all cases, but feel free to lower or increase this number as desired.)

> 📘 Tip: permanently configuring `ulimit -n`
> 
> We recommend permanently setting this by either:
> 
> 1. Adding `ulimit -n 10000` to your `./pants` script.
> 2. Using a tool like [Direnv](https://direnv.net) to run `ulimit -n 10000` everytime the project is loaded.
> 3. Adding `ulimit -n 10000` to your global `.bashrc` or equivalent.
> 
> The first two approaches have the benefit that they will be checked into version control, so every developer at your organization can use the same setting.

> 🚧 macOS users: avoid `ulimit unlimited`
> 
> Contrary to the name, this will not fix the issue. You must use `ulimit -n` instead.

Controlling (test) parallelism
------------------------------

When adopting Pants for your tests you may find that they have issues with being run in parallel, particularly if they are integration tests and use a shared resource such as a database.

To temporarily run a single test at a time (albeit with reduced performance), you can reduce the parallelism globally:

```
./pants --process-execution-local-parallelism=1 test ::
```

A more sustainable solution for shared resources is to use the [`[pytest].execution_slot_var`](doc:reference-pytest#section-execution-slot-var) option, which sets an environment variable which test runs can consume to determine which copy of a resource to consume.

Snap-based Docker
-----------------

In recent Ubuntu distributions, the Docker service is often installed using [Snap](https://snapcraft.io/docker).  
It works mostly same as a normal installation, but has an important difference: it cannot access the `/tmp` directory of the host because it is virtualized when Snap starts the Docker service.

This may cause problems if your code or tests ry to create a container with a bind-mount of a directory or file _under the current working directory_.  Container creation will fail with "invalid mount config for type "bind": bind source path does not exist", because Pants' default `local_execution_root_dir` option is `/tmp`, which the Snap-based Docker service cannot access.

You can work around this issue by explicitly setting `[GLOBAL].local_execution_root_dir` to a directory outside the system `/tmp` directory, such as `"%(buildroot)s/tmp"`.
