# coding=utf-8
# Copyright 2016 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import unittest
import xml.etree.ElementTree as ET
from builtins import object
from textwrap import dedent

from pants.base.build_environment import get_buildroot
from pants.util.contextutil import open_zip, temporary_dir
from pants.util.dirutil import safe_open


SHAPELESS_CLSFILE = 'org/pantsbuild/testproject/unicode/shapeless/ShapelessExample.class'
SHAPELESS_TARGET = 'testprojects/src/scala/org/pantsbuild/testproject/unicode/shapeless'


class BaseZincCompileIntegrationTest(object):

  def create_file(self, path, value):
    with safe_open(path, 'w') as f:
      f.write(value)

  def run_run(self, target_spec, config, workdir):
    args = ['run', target_spec]
    pants_run = self.run_pants_with_workdir(args, workdir, config)
    self.assert_success(pants_run)

  def test_scala_compile_jar(self):
    jar_suffix = 'z.jar'
    with self.do_test_compile(SHAPELESS_TARGET,
                              expected_files=[jar_suffix]) as found:
      with open_zip(self.get_only(found, jar_suffix), 'r') as jar:
        self.assertTrue(jar.getinfo(SHAPELESS_CLSFILE),
                        'Expected a jar containing the expected class.')

  def test_scala_empty_compile(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/emptyscala',
                              expected_files=[]):
      # no classes generated by this target
      pass

  def test_scala_shared_sources(self):
    clsname = 'SharedSources.class'

    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/sharedsources::',
                              expected_files=[clsname]) as found:
      classes = found[clsname]
      self.assertEqual(2, len(classes))
      for cls in classes:
        self.assertTrue(cls.endswith(
          'org/pantsbuild/testproject/sharedsources/SharedSources.class'))

  def test_scala_failure(self):
    """With no initial analysis, a failed compilation shouldn't leave anything behind."""
    analysis_file = 'testprojects.src.scala.' \
        'org.pantsbuild.testproject.compilation_failure.compilation_failure.analysis'
    with self.do_test_compile(
        'testprojects/src/scala/org/pantsbuild/testprojects/compilation_failure',
        expected_files=[analysis_file],
        expect_failure=True) as found:
      self.assertEqual(0, len(found[analysis_file]))

  def test_scala_with_java_sources_compile(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/javasources',
                              expected_files=['ScalaWithJavaSources.class',
                                              'JavaSource.class']) as found:

      self.assertTrue(
          self.get_only(found, 'ScalaWithJavaSources.class').endswith(
              'org/pantsbuild/testproject/javasources/ScalaWithJavaSources.class'))

      self.assertTrue(
          self.get_only(found, 'JavaSource.class').endswith(
              'org/pantsbuild/testproject/javasources/JavaSource.class'))

  def test_scalac_plugin_compile(self):
    with self.do_test_compile(
        'examples/src/scala/org/pantsbuild/example/scalac/plugin:other_simple_scalac_plugin',
        expected_files=['OtherSimpleScalacPlugin.class', 'scalac-plugin.xml']) as found:

      self.assertTrue(
          self.get_only(found, 'OtherSimpleScalacPlugin.class').endswith(
              'org/pantsbuild/example/scalac/plugin/OtherSimpleScalacPlugin.class'))

      # Ensure that the plugin registration file is written to the root of the classpath.
      path = self.get_only(found, 'scalac-plugin.xml')
      self.assertTrue(path.endswith('/classes/scalac-plugin.xml'),
                      'plugin registration file `{}` not located at the '
                      'root of the classpath'.format(path))

      # And that it is well formed.
      root = ET.parse(path).getroot()
      self.assertEqual('plugin', root.tag)
      self.assertEqual('other_simple_scalac_plugin', root.find('name').text)
      self.assertEqual('org.pantsbuild.example.scalac.plugin.OtherSimpleScalacPlugin',
                       root.find('classname').text)

  def test_scalac_debug_symbol(self):
    with self.do_test_compile(
        'examples/src/scala/org/pantsbuild/example/scalac/plugin:simple_scalac_plugin',
        expected_files=['SimpleScalacPlugin.class', 'scalac-plugin.xml'],
        extra_args=['--compile-zinc-debug-symbols']):
      pass

  def test_zinc_unsupported_option(self):
    with self.temporary_workdir() as workdir:
      with self.temporary_cachedir() as cachedir:
        # compile with an unsupported flag
        pants_run = self.run_test_compile(
            workdir,
            cachedir,
            'testprojects/src/scala/org/pantsbuild/testproject/emptyscala',
            extra_args=[
              '--compile-zinc-args=-recompile-all-fraction',
              '--compile-zinc-args=0.5',
            ])
        self.assert_success(pants_run)

        # Confirm that we were warned.
        self.assertIn('is not supported, and is subject to change/removal', pants_run.stdout_data)

  def test_zinc_fatal_warnings(self):
    def test_combination(target, expect_success, extra_args=[]):
      with self.temporary_workdir() as workdir:
        with self.temporary_cachedir() as cachedir:
          pants_run = self.run_test_compile(
              workdir,
              cachedir,
              'testprojects/src/scala/org/pantsbuild/testproject/compilation_warnings:{}'.format(
                target),
              extra_args=extra_args)

          if expect_success:
            self.assert_success(pants_run)
          else:
            self.assert_failure(pants_run)
    test_combination('fatal', expect_success=False)
    test_combination('nonfatal', expect_success=True)

    test_combination('fatal', expect_success=True,
      extra_args=['--compile-zinc-fatal-warnings-enabled-args=[\'-C-Werror\']'])
    test_combination('fatal', expect_success=False,
      extra_args=['--compile-zinc-fatal-warnings-disabled-args=[\'-S-Xfatal-warnings\']'])

  def test_zinc_compiler_options_sets(self):
    def test_combination(target, expect_success, extra_args=[]):
      with self.temporary_workdir() as workdir:
        with self.temporary_cachedir() as cachedir:
          pants_run = self.run_test_compile(
              workdir,
              cachedir,
              'testprojects/src/scala/org/pantsbuild/testproject/compilation_warnings:{}'.format(
                target),
              extra_args=extra_args)

          if expect_success:
            self.assert_success(pants_run)
          else:
            self.assert_failure(pants_run)
    test_combination('fatal', expect_success=False)
    test_combination('nonfatal', expect_success=True)

    test_combination('fatal', expect_success=True,
      extra_args=['--compile-zinc-compiler-option-sets-enabled-args={"fatal_warnings": ["-C-Werror"]}'])
    test_combination('fatal', expect_success=False,
      extra_args=['--compile-zinc-compiler-option-sets-disabled-args={"fatal_warnings": ["-S-Xfatal-warnings"]}'])

  @unittest.expectedFailure
  def test_soft_excludes_at_compiletime(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/exclude_direct_dep',
                              extra_args=['--resolve-ivy-soft-excludes'],
                              expect_failure=True):
      # TODO See #4874. Should have failed to compile because its only dependency is excluded.
      pass

  def test_pool_created_for_fresh_compile_but_not_for_valid_compile(self):
    with self.temporary_cachedir() as cachedir, self.temporary_workdir() as workdir:
      # Populate the workdir.
      first_run = self.run_test_compile(workdir, cachedir,
                            'testprojects/src/scala/org/pantsbuild/testproject/javasources')

      self.assertIn('isolation-zinc-pool-bootstrap', first_run.stdout_data)

      # Run valid compile.
      second_run = self.run_test_compile(workdir, cachedir,
                            'testprojects/src/scala/org/pantsbuild/testproject/javasources')

      self.assertNotIn('isolation-zinc-pool-bootstrap', second_run.stdout_data)

  def test_source_compat_binary_incompat_scala_change(self):
    with temporary_dir() as cache_dir, \
      self.temporary_workdir() as workdir, \
      temporary_dir(root_dir=get_buildroot()) as src_dir:

      config = {
        'cache.compile.zinc': {'write_to': [cache_dir], 'read_from': [cache_dir]},
      }

      srcfile = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'A.scala')
      srcfile_b = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'B.scala')
      buildfile = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'BUILD')

      self.create_file(buildfile,
        dedent("""
                  scala_library(name='a',
                               sources=['A.scala'])
                  scala_library(name='b',
                               sources=['B.scala'],
                               dependencies=[':a'])
                  jvm_binary(name='bin',
                   main='org.pantsbuild.cachetest.B',
                   dependencies=[':b']
                  )
                  """))
      self.create_file(srcfile,
        dedent("""
                          package org.pantsbuild.cachetest
                          object A {
                            def x(y: Option[Int] = None) = {
                              println("x");
                            }
                          }
                          """))

      self.create_file(srcfile_b,
        dedent("""
                                package org.pantsbuild.cachetest
                                object B extends App {
                                  A.x();
                                  System.exit(0);
                                }
                                """))

      cachetest_bin_spec = os.path.join(os.path.basename(src_dir), 'org', 'pantsbuild',
        'cachetest:bin')
      cachetest_spec = cachetest_bin_spec

      # Caches values A.class, B.class
      self.run_run(cachetest_spec, config, workdir)

      self.create_file(srcfile,
        dedent("""
                          package org.pantsbuild.cachetest;
                          object A {
                            def x(y: Option[Int] = None, z:Option[Int]=None) = {
                              println("x");
                            }
                          }
                          """))
      self.run_run(cachetest_bin_spec, config, workdir)

  def test_source_compat_binary_incompat_java_change(self):
    with temporary_dir() as cache_dir, \
      self.temporary_workdir() as workdir, \
      temporary_dir(root_dir=get_buildroot()) as src_dir:

      config = {
        'cache.compile.zinc': {'write_to': [cache_dir], 'read_from': [cache_dir]},
        'compile.zinc': {'incremental_caching': True },
      }

      srcfile = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'A.java')
      srcfile_b = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'B.java')
      buildfile = os.path.join(src_dir, 'org', 'pantsbuild', 'cachetest', 'BUILD')

      self.create_file(buildfile,
        dedent("""
                  java_library(name='cachetest',
                               sources=['A.java'])
                  java_library(name='b',
                               sources=['B.java'],
                               dependencies=[':a']
                               )
                  jvm_binary(name='bin',
                      main='org.pantsbuild.cachetest.B',
                      dependencies=[':b']
                     )
                  """))
      self.create_file(srcfile,
        dedent("""package org.pantsbuild.cachetest;
                          class A {
                            public static void x() {
                              System.out.println("x");
                            }
                          }
                          """))

      self.create_file(srcfile_b,
        dedent("""package org.pantsbuild.cachetest;
                                class B {
                                  public static void main(String[] args) {
                                    A.x();
                                  }
                                }
                                """))

      cachetest_spec = os.path.join(os.path.basename(src_dir), 'org', 'pantsbuild',
        'cachetest:cachetest')

      self.run_run(cachetest_spec, config, workdir)

      self.create_file(srcfile,
        dedent("""package org.pantsbuild.cachetest;
                                class A {
                                  public static int x() {
                                    System.out.println("x");
                                    return 0;
                                  }
                                }
                                """))

      self.run_run(cachetest_spec, config, workdir)
