import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import Editor from "@monaco-editor/react";
import ReactMarkdown from "react-markdown";
import { Play, Send, ChevronLeft, Moon, Sun, Settings } from "lucide-react";

export default function Workspace() {
  const { slug } = useParams();
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [theme, setTheme] = useState("vs-dark");
  const [output, setOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState("testcases");

  useEffect(() => {
    fetch(`/coding/api/problems/${slug}`)
      .then((res) => res.json())
      .then((data) => {
        setProblem(data);
        
        // Provide standard input/output boilerplate for each language
        if (language === "python") {
          setCode(`import sys\n\ndef solve():\n    # Read all input from standard input\n    input_data = sys.stdin.read().strip()\n    \n    # TODO: Write your logic here\n    # result = ...\n    \n    # Print the result to standard output\n    # print(result)\n\nif __name__ == '__main__':\n    solve()`);
        } else if (language === "javascript") {
          setCode(`const fs = require('fs');\n\nfunction solve() {\n    // Read all input from standard input\n    const inputData = fs.readFileSync('/dev/stdin', 'utf-8').trim();\n    \n    // TODO: Write your logic here\n    // const result = ...;\n    \n    // Print the result\n    // console.log(result);\n}\n\nsolve();`);
        } else if (language === "c") {
          setCode(`#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint main() {\n    // Example: Read a string from standard input\n    char input_data[1024];\n    if (scanf("%s", input_data) == 1) {\n        // TODO: Write your logic here\n        \n        // Print the result\n        // printf("result\\n");\n    }\n    return 0;\n}`);
        } else if (language === "cpp") {
          setCode(`#include <iostream>\n#include <string>\nusing namespace std;\n\nint main() {\n    string input_data;\n    if (cin >> input_data) {\n        // TODO: Write your logic here\n        \n        // Print the result\n        // cout << "result" << endl;\n    }\n    return 0;\n}`);
        } else if (language === "java") {
          setCode(`import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        if (scanner.hasNext()) {\n            String inputData = scanner.next();\n            \n            // TODO: Write your logic here\n            \n            // Print the result\n            // System.out.println("result");\n        }\n        scanner.close();\n    }\n}`);
        }
      });
  }, [slug, language]);

  const handleRun = async () => {
    setIsRunning(true);
    setActiveTab("console");
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      const res = await fetch("/coding/api/submit", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          problem_id: problem.id,
          language,
          code,
        }),
      });
      const data = await res.json();
      setOutput(`Verdict: ${data.verdict}\nRuntime: ${data.runtime}s\nMemory: ${data.memory}KB\n\nOutput:\n${data.output || ""}`);
    } catch (e) {
      setOutput("Error executing code.");
    } finally {
      setIsRunning(false);
    }
  };

  if (!problem) return <div className="p-8 flex justify-center items-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;

  return (
    <div className="h-[calc(100vh-64px)] flex flex-col bg-gray-50 dark:bg-[#1e1e1e] text-gray-900 dark:text-gray-100">
      {/* Navbar */}
      <div className="h-14 flex items-center justify-between px-4 border-b dark:border-gray-800 bg-white dark:bg-[#1e1e1e] shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/coding" className="text-gray-500 hover:text-gray-900 dark:hover:text-white">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-semibold text-lg">{problem.title}</h1>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-gray-100 dark:bg-gray-800 border-none rounded px-3 py-1 text-sm outline-none"
          >
            <option value="python">Python</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
            <option value="java">Java</option>
            <option value="javascript">JavaScript</option>
          </select>
          <button
            onClick={() => setTheme(theme === "vs-dark" ? "light" : "vs-dark")}
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
          >
            {theme === "vs-dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 rounded text-sm font-medium transition"
          >
            <Play className="w-4 h-4 text-green-500" />
            Run
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition"
          >
            <Send className="w-4 h-4" />
            Submit
          </button>
        </div>
      </div>

      {/* Workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Description */}
        <div className="w-[45%] flex flex-col bg-white dark:bg-[#1e1e1e] border-r dark:border-gray-800">
          <div className="p-6 overflow-y-auto h-full prose dark:prose-invert max-w-none">
            <div className="flex items-center gap-3 mb-4">
              <span
                className={`px-2 py-1 rounded text-xs font-semibold ${
                  problem.difficulty === "Easy"
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    : problem.difficulty === "Medium"
                    ? "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                    : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                }`}
              >
                {problem.difficulty}
              </span>
            </div>
            <ReactMarkdown>{problem.description || "No description provided."}</ReactMarkdown>
          </div>
        </div>

        {/* Right Panel: Editor & Output */}
        <div className="w-[55%] flex flex-col min-w-0">
          <div className="flex-1 relative">
            <Editor
              height="100%"
              language={language === "cpp" ? "cpp" : language}
              theme={theme}
              value={code}
              onChange={(val) => setCode(val || "")}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                padding: { top: 16 },
                scrollBeyondLastLine: false,
              }}
            />
          </div>

          {/* Bottom Panel: Console/Testcases */}
          <div className="h-64 bg-white dark:bg-[#1e1e1e] flex flex-col border-t dark:border-gray-800 shrink-0">
            <div className="flex items-center px-4 border-b dark:border-gray-800 shrink-0">
              <button
                onClick={() => setActiveTab("testcases")}
                className={`px-4 py-2 text-sm font-medium border-b-2 ${
                  activeTab === "testcases"
                    ? "border-indigo-500 text-indigo-500"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}
              >
                Test Cases
              </button>
              <button
                onClick={() => setActiveTab("console")}
                className={`px-4 py-2 text-sm font-medium border-b-2 ${
                  activeTab === "console"
                    ? "border-indigo-500 text-indigo-500"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}
              >
                Console Output
              </button>
            </div>
            <div className="p-4 flex-1 overflow-y-auto font-mono text-sm">
              {activeTab === "testcases" ? (
                <div className="space-y-4">
                  {problem.test_cases?.map((tc, idx) => (
                    <div key={tc.id} className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded">
                      <div className="font-semibold mb-2">Case {idx + 1}</div>
                      <div className="mb-2">
                        <span className="text-gray-500">Input:</span>
                        <pre className="mt-1 bg-white dark:bg-gray-900 p-2 rounded border dark:border-gray-700">
                          {tc.input_data}
                        </pre>
                      </div>
                      <div>
                        <span className="text-gray-500">Expected Output:</span>
                        <pre className="mt-1 bg-white dark:bg-gray-900 p-2 rounded border dark:border-gray-700">
                          {tc.expected_output}
                        </pre>
                      </div>
                    </div>
                  ))}
                  {(!problem.test_cases || problem.test_cases.length === 0) && (
                    <div className="text-gray-500">No visible test cases.</div>
                  )}
                </div>
              ) : (
                <pre className="whitespace-pre-wrap">{output || "Run your code to see output here."}</pre>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
