Blablabla, answer some questions and we'll do everything for you. Now let's get started


# Which one of the following version control systems do you use?
 - None
 - git
 - svn
 - mercurial
 - ...

# What programming language(s) is your project based on? - None
 - None
 - Python
 - Ruby
 - Javascript
 - ....

# Which one of following linters do you use? (options based on the language)
 - None
 - ...

# How do you build your software? (options based on the language)
 - No building
 - python setup.py
 ...

# Do you run any of the following testig commands? (options based on the language)

# Packaging?


# Tweak the steps.

Edit, Add, remove, re-order

fill in the commands you would use.
(multi-part step - ommit the command)

[clone][git clone]
[lint][flake8]
[build][setup]
[test][tox]
[package][tar]


# Who should do what?
Upload Public Keys
associate keys with steps (who does what)


# Do a dry run to produce data that we can use to generate the layout


```
in-toto-run ....
in-toto-run ....
in-toto-record start ....

# do your stuff here

in-toto-record stop ....
in-toto-run ....
in-toto-run ....
in-toto-run ....
```

#. Upload the data
...

If names don't match names from before either go back to (tweak steps) or upload
correct link files.


#. Your layout is finished
Big button to download the layout

or use the web editor.

#. Were to go from here

- sign the layout
- tell your guys to wrap their commands with in-toto commands

