import { useState, useEffect } from "react";
import { Users, Code, Activity, Server } from "lucide-react";

export default function AdminDashboard() {
  const [students, setStudents] = useState([]);
  const [problems, setProblems] = useState([]);

  useEffect(() => {
    fetch("/admin/api/coding/students")
      .then((res) => res.json())
      .then(setStudents);
      
    fetch("/admin/api/coding/problems")
      .then((res) => res.json())
      .then(setProblems);
  }, []);

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 dark:bg-gray-900 min-h-screen text-gray-900 dark:text-gray-100">
      <h1 className="text-3xl font-bold mb-8">Coding Practice Analytics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex items-center gap-4 border-l-4 border-indigo-500">
          <div className="p-3 bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-300 rounded-full">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm text-gray-500">Active Students</div>
            <div className="text-2xl font-bold">{students.length}</div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex items-center gap-4 border-l-4 border-green-500">
          <div className="p-3 bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-300 rounded-full">
            <Code className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Problems</div>
            <div className="text-2xl font-bold">{problems.length}</div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex items-center gap-4 border-l-4 border-yellow-500">
          <div className="p-3 bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-300 rounded-full">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Submissions</div>
            <div className="text-2xl font-bold">
              {students.reduce((acc, s) => acc + s.total_submissions, 0)}
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex items-center gap-4 border-l-4 border-blue-500">
          <div className="p-3 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm text-gray-500">Judge0 Status</div>
            <div className="text-2xl font-bold text-green-500">Online</div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden mb-8">
        <div className="p-4 border-b dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <h2 className="text-lg font-semibold">Student Leaderboard / Activity</h2>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b dark:border-gray-700 text-sm text-gray-500">
              <th className="p-4">Student</th>
              <th className="p-4">Email</th>
              <th className="p-4">Problems Solved</th>
              <th className="p-4">Total Submissions</th>
              <th className="p-4">Success Rate</th>
            </tr>
          </thead>
          <tbody>
            {students.sort((a, b) => b.total_solved - a.total_solved).map((student) => (
              <tr key={student.id} className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750">
                <td className="p-4 font-medium">{student.username}</td>
                <td className="p-4 text-gray-500">{student.email}</td>
                <td className="p-4 text-green-500 font-semibold">{student.total_solved}</td>
                <td className="p-4">{student.total_submissions}</td>
                <td className="p-4">
                  {student.total_submissions > 0
                    ? Math.round((student.total_solved / student.total_submissions) * 100)
                    : 0}%
                </td>
              </tr>
            ))}
            {students.length === 0 && (
              <tr>
                <td colSpan="5" className="p-8 text-center text-gray-500">No active students found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
