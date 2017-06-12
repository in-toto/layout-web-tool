collection = {
  "vcs": [{
    "type": "",
    "prog_lang": "",
    "name": "Git",
    "logo": "https://git-scm.com/images/logos/downloads/Git-Icon-1788C.png",
    "cmd": "git clone [url]"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "SVN",
    "logo": "https://linuxanswer.org/wp-content/uploads/2017/03/svn.png",
    "cmd": "svn checkout/co URL PATH"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Mercurial",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/New_Mercurial_logo.svg/2000px-New_Mercurial_logo.svg.png",
    "cmd": "hg clone --uncompressed http://server/repo"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "GNU Bazaar ",
    "logo": "http://2.bp.blogspot.com/-Yqd0z4K94B0/TfSS8OXf89I/AAAAAAAABJA/fGLt-N9ti2s/s200/bazaar.png",
    "cmd": "bzr branch lp:bzr bzr.dev"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Monotone",
    "logo": "https://www.monotone.ca/res/logo.png",
    "cmd": "mtn db init --db=:user"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Fossil",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Fossil_SCM_logo.svg/170px-Fossil_SCM_logo.svg.png",
    "cmd": "fossil clone ?OPTIONS? URI FILENAME"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Darcs",
    "logo": "http://darcs.net/img/logos/logo.png",
    "cmd": "darcs clone --lazy URL"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "CVS",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d8/TortoiseCVS_Logo.png",
    "cmd": "cvs -d /home/Project/CVS_root init"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "AccuRev",
    "logo": "https://pbs.twimg.com/profile_images/378800000092420461/aeab81f94d12ea387f7cae8868892112_400x400.png",
    "cmd": "accurev mkstream -s <stream> -b <backing-stream>"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Veracity",
    "logo": "https://discoversdkcdn.azureedge.net/runtimecontent/companyfiles/5875/3191/thumbnail.png",
    "cmd": ""
  }, {
    "type": "",
    "prog_lang": "",
    "name": "ArX",
    "logo": "https://arxequity.com/wp-content/themes/arx/img/logo_big_blue.png",
    "cmd": "arx make-archive ArchiveName RepositoryDirectory"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "BitKeeper",
    "logo": "http://www.bitkeeper.org/man/BitKeeper_SN_Blue.png",
    "cmd": "bk clone <from>"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "SVK",
    "logo": "",
    "cmd": "svk commit [PATH\u2026]"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Plastic SCM",
    "logo": "https://pbs.twimg.com/profile_images/378800000542266610/114e3495e712c5bc736970326ecfb9f2_400x400.png",
    "cmd": "cm mkwk [name]"
  }, {
    "type": "",
    "prog_lang": "",
    "name": "Team Foundation Server",
    "logo": "https://szul.blob.core.windows.net/images/team-foundation-server-2015-header.png",
    "cmd": "tf get [itemspec]"
  }],
  "building": [{
    "type": "make_based",
    "prog_lang": "",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Tux.svg/150px-Tux.svg.png",
    "name": "make",
    "cmd": "make [-einpqrst] [-f makefile]... [-k|-S] [macro=value...] [target_name...]"
  }, {
    "type": "build_script_generation",
    "prog_lang": "",
    "logo": "",
    "name": "configure",
    "cmd": "./configure"
  }, {
    "type": "non_make_based",
    "prog_lang": "Java, C, C++",
    "logo": "http://antinstaller.sourceforge.net/manual/images/ant_logo_large.gif",
    "name": "Apache ANT",
    "cmd": "install, init, all"
  }, {
    "type": "non_make_based",
    "prog_lang": "",
    "logo": "http://www.scala-sbt.org/assets/typesafe_sbt_svg.svg",
    "name": "Scala Simple Build Tool",
    "cmd": "compile"
  }, {
    "type": "non_make_based",
    "prog_lang": "MS Visual Studio, C++",
    "logo": "http://www.eitcafe.com/wp-content/uploads/2016/07/msbuild.jpg",
    "name": "MS Build",
    "cmd": "MSBuild.exe MyProj.proj /property:Configuration=Debug , cl /EHsc hello.cpp"
  }, {
    "type": "non_make_based",
    "prog_lang": "Ruby",
    "logo": "",
    "name": "Rake",
    "cmd": "rake"
  }, {
    "type": "",
    "prog_lang": "XML(Project Object Model)",
    "logo": "https://maven.apache.org/images/maven-logo-black-on-white.png",
    "name": "Maven",
    "cmd": "mvn compile"
  }, {
    "type": "non_make_based",
    "prog_lang": "Python",
    "logo": "http://scons.org/images/SCons.png",
    "name": "Scons",
    "cmd": "scons foo.out"
  }],
  "qa": [{
    "type": "Unit Testing",
    "prog_lang": "C",
    "name": "Check",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C",
    "name": "AceUnit",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C#",
    "name": "csUnit",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C#",
    "name": "Visual Studio Unit Testing Framework",
    "logo": "http://www.qatestingtools.com/sites/default/files/tools_shortcuts/Visual%20Studio%20Unite%20Testing%20Framework%20150.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C++",
    "name": "Parasoft C/C++test",
    "logo": "https://discoversdkcdn.azureedge.net/runtimecontent/companyfiles/5703/1899/thumbnail.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C++",
    "name": "CppUnit",
    "logo": "http://www.howcsharp.com/img/0/9/cppunit-300x225.jpg",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Haskell",
    "name": "HUnit",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Haskell",
    "name": "QuickCheck",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Java",
    "name": "JUnit",
    "logo": "http://www.swtestacademy.com/wp-content/uploads/2015/11/Junit_Logo.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Java",
    "name": "Jtest",
    "logo": "http://www.bj-zhzt.com/datacache/pic/390_260_b91e82190f00f190d60d78bf53f6352b.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "JavaScript",
    "name": "Jasmine",
    "logo": "https://upload.wikimedia.org/wikipedia/en/thumb/2/22/Logo_jasmine.svg/1028px-Logo_jasmine.svg.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "JavaScript",
    "name": "Unit.js",
    "logo": "https://upload.wikimedia.org/wikipedia/en/e/ec/Unit_JS_logo.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "PHP",
    "name": "SimpleTest",
    "logo": "http://www.simpletest.org/images/simpletest-logo.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "PHP",
    "name": "PHPUnit",
    "logo": "http://4.bp.blogspot.com/-xrvHPUBqc7Y/Ucxe5ZYDVYI/AAAAAAAAAVE/cXtFm0NcE9A/s500/logo.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Python",
    "name": "unittest",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Python",
    "name": "doctest",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "R",
    "name": "RUnit",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "R",
    "name": "testthat",
    "logo": "https://d21ii91i3y6o6h.cloudfront.net/gallery_images/from_proof/13597/small/1466619792/rstudio-hex-testthat.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Scala",
    "name": "ScalaTest",
    "logo": "http://media.tumblr.com/ec3c87095fe8a21216c516606afffdcc/tumblr_inline_mtskzebUcv1s17bu5.jpg",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "Scala",
    "name": "ScUnit",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "all",
    "name": "Travis CI",
    "logo": "https://cdn.travis-ci.com/images/logos/TravisCI-Mascot-1-20feeadb48fc2492ba741d89cb5a5c8a.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "Java",
    "name": "Jenkins",
    "logo": "https://www.cloudbees.com/sites/default/files/Jenkins_8.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "Java",
    "name": "TeamCity",
    "logo": "http://workingwithdevs.com/wp-content/uploads/2014/05/TeamCity-logo.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "all",
    "name": "Bamboo",
    "logo": "https://www.vectorcast.com/sites/default/themes/vectorsoftware/images/Bamboo-logo_clipped.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "all",
    "name": "Codeship",
    "logo": "http://rixrix.github.io/ci-talk-codeship/images/logo_codeship_colour.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "all",
    "name": "CircleCI",
    "logo": "https://circleci.com/circleci-logo-stacked-fb.png",
    "cmd": ""
  }, {
    "type": "Continuous Integration",
    "prog_lang": "all",
    "name": "Buildbot",
    "logo": "https://buildbot.net/img/nut.png",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "Python",
    "name": "Pylint",
    "logo": "https://carlchenet.com/wp-content/uploads/2013/08/pylint-logo.png",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "Python",
    "name": "Flake8",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "Python",
    "name": "PyChecker",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "Java",
    "name": "Checkstyle",
    "logo": "http://checkstyle.sourceforge.net/images/header-checkstyle-logo.png",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "Java",
    "name": "Coverity",
    "logo": "https://2015.appsecusa.org/c/wp-content/uploads/2014/07/coveritylogo.png",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "C/C++",
    "name": "Lint",
    "logo": "",
    "cmd": ""
  }, {
    "type": "Linting",
    "prog_lang": "C/C++",
    "name": "Cppcheck",
    "logo": "https://cdn.portableapps.com/CppcheckPortable_128.png",
    "cmd": ""
  }, {
    "type": "Unit Testing",
    "prog_lang": "C",
    "name": "Check",
    "logo": "",
    "cmd": ""
  }, ],
  "package": [{
    "type": "",
    "prog_lang": "",
    "logo": "",
    "name": "Tar",
    "cmd": "tar -cvf afiles.tar file1 file2 file3"
  }, {
    "type": "",
    "prog_lang": "",
    "logo": "",
    "name": "Zip",
    "cmd": ""
  }, {
    "type": "",
    "prog_lang": "",
    "logo": "",
    "name": "Wheel",
    "cmd": "python setup.py bdist_wheel"
  }, {
    "type": "",
    "prog_lang": "",
    "logo": "",
    "name": "MSI",
    "cmd": ""
  }]
}