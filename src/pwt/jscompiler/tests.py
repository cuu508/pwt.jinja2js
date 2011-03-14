import unittest
from cStringIO import StringIO

import soy_wsgi

import jinja2.compiler
import jinja2.nodes
import jinja2.optimizer
import jinja2.runtime

import jscompiler


def generateMacro(
        node, environment, name, filename, stream, autoescape = False):
    generator = jscompiler.MacroCodeGenerator(environment, None, None, stream)
    eval_ctx = jinja2.nodes.EvalContext(environment, name)
    eval_ctx.namespace = "test"
    eval_ctx.autoescape = autoescape
    generator.blockvisit(node.body, jscompiler.JSFrame(environment, eval_ctx))


class JSCompilerTemplateTestCase(unittest.TestCase):

    def setUp(self):
        super(JSCompilerTemplateTestCase, self).setUp()

        self.loader = jinja2.PackageLoader("pwt.jscompiler", "test_templates")
        self.env = jinja2.Environment(
            loader = self.loader,
            extensions = ["pwt.jscompiler.jscompiler.Namespace"],
            )

    def get_compile_from_string(self, source, name = None, filename = None):
        node = self.env._parse(source, name, filename)
        # node = jinja2.optimizer.optimize(node, self.env)

        return node

    def test_missing_namespace1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        stream = StringIO()
        self.assertRaises(jinja2.compiler.TemplateAssertionError, jscompiler.generate, node, self.env, "", "", stream = stream)

    def test_const1(self):
        node = self.get_compile_from_string("""{% macro hello() %}
Hello, world!
{% endmacro %}""")
        stream = StringIO()
        generateMacro(
            node, self.env, "const.html", "const.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, world!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var1(self):
        node = self.get_compile_from_string("""{% macro hello(name) %}
{{ name }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var1.html", "var1.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', opt_data.name, '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var2(self):
        node = self.get_compile_from_string("""{% macro helloName(name) %}
Hello, {{ name }}!
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.helloName = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\nHello, ', opt_data.name, '!\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var3(self):
        # variables with numerical addition
        node = self.get_compile_from_string("""{% macro add(num) %}
{{ num + 200 }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num + 200), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var4(self):
        # variables with numerical addition to variable
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num + step }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num + opt_data.step), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var5(self):
        # variables minus, power of, 
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ (num - step) ** 2 }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', Math.pow((opt_data.num - opt_data.step), 2), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var6(self):
        # variables floor division
        node = self.get_compile_from_string("""{% macro fd(n1, n2) %}
{{ Math.floor(n1 / n2) }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', Math.floor((opt_data.num / opt_data.step)), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var6(self):
        # variables minus, power of, 
        node = self.get_compile_from_string("""{% macro add(num, step) %}
{{ num - (step ** 2) }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', (opt_data.num - Math.pow(opt_data.step, 2)), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_var7(self):
        # variables + with autoescape on
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ num - (step ** 2) }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((opt_data.num - Math.pow(opt_data.step, 2))));
    if (!opt_sb) return output.toString();
}""")

    def test_var8(self):
        # variables + with autoescape and the escape filter
        node = self.get_compile_from_string("""{% macro add(num, step) %}{{ (num - (step ** 2)) | escape }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((opt_data.num - Math.pow(opt_data.step, 2))));
    if (!opt_sb) return output.toString();
}""")

    def test_var9(self):
        # variables -
        node = self.get_compile_from_string("""{% macro add(num) %}{{ -num + 20 }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(((-opt_data.num) + 20)));
    if (!opt_sb) return output.toString();
}""")

    def test_var10(self):
        # variables +
        node = self.get_compile_from_string("""{% macro add(num) %}{{ +num + 20 }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(((+opt_data.num) + 20)));
    if (!opt_sb) return output.toString();
}""")

    def test_var11(self):
        # variables not
        node = self.get_compile_from_string("""{% macro add(bool) %}{{ not bool }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "var2.html", "var2.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.add = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml((!opt_data.bool)));
    if (!opt_sb) return output.toString();
}""")

    def test_for1(self):
        # XXX - test recursive loop
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro fortest(data) %}
{% for item in data %}
  Item {{ item }}.
{% else %}
  No items.
{% endfor %}
{% endmacro %}
""")
        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');

xxx.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    if (itemListLen > 0) {
        for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
            var itemData = itemList[itemIndex];
            output.append('\\n  Item ', itemData, '.\\n');
        }
    } else {
        output.append('\\n  No items.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for2(self):
        # test loop.index0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index0 }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for3(self):
        # test loop.index variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.index }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for4(self):
        # test loop.revindex & loop.revindex0 variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.revindex }} - {{loop.revindex0 }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen - itemIndex - 1, ' - ', itemListLen - itemIndex);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for5(self):
        # test loop.length & loop.first & loop.last variables
        node = self.get_compile_from_string("{% macro fortest(data) %}{% for item in data %}{{ loop.length }} - {{loop.first }} - {{ loop.last }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemListLen, ' - ', itemIndex == 0, ' - ', itemIndex == (itemListLen - 1));
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for6(self):
        # test invalid loop access
        node = self.get_compile_from_string("{% namespace xxx %}{% macro fortest(data) %}{% for item in data %}{{ loop.missing }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        self.assertRaises(
            AttributeError,
            jscompiler.generate,
            node, self.env, "for.html", "for.html", stream = stream)

    def test_for7(self):
        # test loop.index with other variable.
        node = self.get_compile_from_string("{% macro fortest(data, name) %}{% for item in data %}{{ loop.index }} - {{ name }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.name);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for8(self):
        # test loop.index with other variable, with attribute
        node = self.get_compile_from_string("{% macro fortest(data, param) %}{% for item in data %}{{ loop.index }} - {{ param.name }}{% endfor %}{% endmacro %}")
        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    var itemList = opt_data.data;
    var itemListLen = itemList.length;
    for (var itemIndex = 0; itemIndex < itemListLen; itemIndex++) {
        var itemData = itemList[itemIndex];
        output.append(itemIndex + 1, ' - ', opt_data.param.name);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_for9(self):
        # bug report - need to rename nested for loop iterators.
        node = self.get_compile_from_string("""{% macro fortest(jobs) %}
{% for job in jobs %}
   {% for badge in job.badges %}
       {{ badge.name }}
   {% endfor %}
{% endfor %}
{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.fortest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var jobList = opt_data.jobs;
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append('\\n   ');
        var badgeList = jobData.badges;
        var badgeListLen = badgeList.length;
        for (var badgeIndex = 0; badgeIndex < badgeListLen; badgeIndex++) {
            var badgeData = badgeList[badgeIndex];
            output.append('\\n       ', badgeData.name, '\\n   ');
        }
        output.append('\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_for10(self):
        # test for in list loop
        node = self.get_compile_from_string("""{% macro forinlist(jobs) %}
{% for job in [1, 2, 3] %}
   {{ job }}
{% endfor %}
{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.forinlist = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    var jobList = [1, 2, 3];
    var jobListLen = jobList.length;
    for (var jobIndex = 0; jobIndex < jobListLen; jobIndex++) {
        var jobData = jobList[jobIndex];
        output.append('\\n   ', jobData, '\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_if1(self):
        # test if
        node = self.get_compile_from_string("""{% macro testif(option) %}{% if option %}{{ option }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if2(self):
        # test if / else
        node = self.get_compile_from_string("""{% macro iftest(option) %}
{% if option %}
Option set.
{% else %}
No option.
{% endif %}
{% endmacro %}
""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.iftest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n');
    if (opt_data.option) {
        output.append('\\nOption set.\\n');
    } else {
        output.append('\\nNo option.\\n');
    }
    output.append('\\n');
    if (!opt_sb) return output.toString();
}""")

    def test_if3(self):
        # test if ==
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num == 0 %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.num == 0) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if4(self):
        # test if == and !=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num != 0 and num == 2 %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((opt_data.num != 0 && opt_data.num == 2)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if5(self):
        # test if > and >= and < and <=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num > 0 and num >= 1 and num < 2 and num <= 3 %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((((opt_data.num > 0 && opt_data.num >= 1) && opt_data.num < 2) && opt_data.num <= 3)) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_if6(self):
        # test if in
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num in [1, 2, 3] %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "if.html", "if.html", stream = stream)

    def test_if7(self):
        # test if in
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num not in [1, 2, 3] %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            generateMacro, node, self.env, "if.html", "if.html", stream = stream)

    def test_if8(self):
        # test if > and >= and < and <=
        node = self.get_compile_from_string("""{% macro testif(num) %}{% if num + 1 == 2 %}{{ num }}{% endif %}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "if.html", "if.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if ((opt_data.num + 1) == 2) {
        output.append(opt_data.num);
    }
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro1(self):
        # call macro in same template, without arguments.
        node = self.get_compile_from_string("""{% namespace xxx %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.testif() }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx');
goog.require('soy');

xxx.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro2(self):
        # call macro in same template where the namespace contains
        # multiple dotted names.
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif() }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro3(self):
        # call macro passing in a argument
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.testif(option = true) }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.testif({option: true}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro4(self):
        # call macro passing parament, with extra output
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(option = true) }}!{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.testif = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    if (opt_data.option) {
        output.append(opt_data.option);
    }
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    xxx.ns1.testif({option: true}, output);
    output.append('!');
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro5(self):
        # call macro with positional arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}
{% macro testcall() %}Hello, {{ xxx.ns1.testif(true) }}!{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generate, node, self.env, "", "", stream = stream)

    def test_call_macro6(self):
        # call macro with dynamic keywrod arguments
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro testif(option) -%}
{% if option %}{{ option }}{% endif %}{% endmacro %}

{% macro testcall() %}Hello, {{ xxx.ns1.testif(**{option: true}) }}!{% endmacro %}""")

        stream = StringIO()
        self.assertRaises(
            jinja2.compiler.TemplateAssertionError,
            jscompiler.generate, node, self.env, "", "", stream = stream)

    def test_call_macro7(self):
        # call macro with string keyword
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = "Michael") }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.hello({name: 'Michael'}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_call_macro8(self):
        # call macro with parameter sub
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% macro hello(name) -%}
Hello, {% if name %}{{ name.first }}{% else %}world{% endif %}!{% endmacro %}

{% macro testcall() %}{{ xxx.ns1.hello(name = {"first": "Michael"}) }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');

xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('Hello, ');
    if (opt_data.name) {
        output.append(opt_data.name.first);
    } else {
        output.append('world');
    }
    output.append('!');
    if (!opt_sb) return output.toString();
}


xxx.ns1.testcall = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    xxx.ns1.hello({name: {'first': 'Michael'}}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_import1(self):
        node = self.get_compile_from_string("""{% namespace xxx.ns1 %}
{% import 'test_import.soy' as forms %}

{% macro hello(name) %}{{ forms.input(name = 'test') }}{% endmacro %}""")

        stream = StringIO()
        jscompiler.generate(
            node, self.env, "for.html", "for.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """goog.provide('xxx.ns1');
goog.require('soy');


goog.require('test.ns1');


xxx.ns1.hello = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    test.ns1.input({name: 'test'}, output);
    if (!opt_sb) return output.toString();
}""")

    def test_filter_escape1(self):
        # escape filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|escape }}{% endmacro %}""")
        stream = StringIO()
        generateMacro(node, self.env, "filter.html", "filter.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(opt_data.data));
    if (!opt_sb) return output.toString();
}""")

    def test_filter_escape2(self):
        # autoescape filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data }}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "filter.html", "filter.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(soy.$$escapeHtml(opt_data.data));
    if (!opt_sb) return output.toString();
}""")

    def test_filter_escape3(self):
        # autoescape with safe filter
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|safe }}{% endmacro %}""")

        stream = StringIO()
        generateMacro(node, self.env, "filter.html", "filter.html", stream = stream, autoescape = True)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(opt_data.data);
    if (!opt_sb) return output.toString();
}""")

    def XXXtest_filter1(self):
        # test filter without kwargs
        node = self.get_compile_from_string("""{% macro filtertest(data) %}
{{ data|title() }}
{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "filter.html", "filter.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append('\\n', jinja2_filters.filter_title(opt_data.data), '\\n');
    if (!opt_sb) return output.toString();
}""")

    def XXXtest_filter2(self):
        # XXX - test filter with kwargs
        node = self.get_compile_from_string("""{% macro filtertest(data) %}{{ data|truncate(length=280, killwords=False) }}{% endmacro %}
""")
        stream = StringIO()
        generateMacro(node, self.env, "filter.html", "filter.html", stream = stream)
        source_code = stream.getvalue()

        self.assertEqual(source_code, """test.filtertest = function(opt_data, opt_sb) {
    var output = opt_sb || new soy.StringBuilder();
    output.append(jinja2_filters.filter_truncate(opt_data.data, {length: 280, killwords: false}));
    if (!opt_sb) return output.toString();
}""")


class JSCompilerTemplateTestCaseOptimized(JSCompilerTemplateTestCase):

    def get_compile_from_string(self, source, name = None, filename = None):
        node = super(JSCompilerTemplateTestCaseOptimized, self).get_compile_from_string(source, name, filename)
        node = jinja2.optimizer.optimize(node, self.env)

        return node


import webtest

class SoyServer(unittest.TestCase):

    def get_app(self):
        return webtest.TestApp(
            soy_wsgi.Resources(
                url = "/soy/", packages = "pwt.jscompiler:test_templates"))

    def test_soy1(self):
        app = self.get_app()
        self.assertRaises(webtest.AppError, app.get, "/soy/missing.soy")

    def test_soy2(self):
        app = self.get_app()
        res = app.get("/soy/example.soy")
