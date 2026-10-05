// Theme Toggle with Local Storage
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Update line numbers for editor
function updateLineNumbers() {
    const editor = document.getElementById('editor');
    const lineNumbers = document.querySelector('.line-numbers');
    if (!editor || !lineNumbers) return;
    
    const lines = editor.value.split('\n').length;
    let numbersHtml = '';
    for (let i = 1; i <= Math.max(lines, 7); i++) {
        numbersHtml += `<span>${i}</span>`;
    }
    lineNumbers.innerHTML = numbersHtml;
}

// Load saved theme and initialize editor
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
    } else {
        document.body.classList.add('dark-mode');
    }
    
    const editor = document.getElementById('editor');
    if (editor) {
        // Auto-update line numbers on textarea input
        editor.addEventListener('input', updateLineNumbers);
        
        // Trigger initial line numbers
        updateLineNumbers();
        
        // Support tab key in editor
        editor.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                this.value = this.value.substring(0, start) + "    " + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
                updateLineNumbers();
            }
        });
    }
});

// Toast notification function
function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Logic Execution with UI Feedback
function runCode() {
    const btn = document.getElementById('runCodeBtn');
    const stat = document.getElementById('res-stat');
    const resVal = document.getElementById('res-val');
    
    if (!btn || !stat || !resVal) return;
    
    // Simulate loading state
    btn.classList.add('running');
    btn.querySelector('span').innerText = 'Running...';
    stat.className = 'status-badge pending';
    stat.innerText = 'Running...';
    resVal.innerText = '--';
    resVal.classList.add('text-muted');
    
    // Artificial delay to show dynamic UI (800ms)
    setTimeout(() => {
        const input = 145; // Simulated input
        
        // Logic execution
        const fact = n => n <= 1 ? 1 : n * fact(n - 1);
        const sum = String(input).split('').reduce((a, b) => a + fact(Number(b)), 0);
        
        const isStrong = (sum === input);
        
        // UI Update
        resVal.innerText = isStrong ? "Strong Number" : "Not Strong";
        resVal.classList.remove('text-muted');
        
        stat.className = isStrong ? 'status-badge passed' : 'status-badge failed';
        stat.innerText = isStrong ? "Passed" : "Failed";
        
        // Reset Button
        btn.classList.remove('running');
        btn.querySelector('span').innerText = 'Run Code';
        
        // Show Toast
        showToast(`Execution completed! Test ${isStrong ? 'passed' : 'failed'}.`);
        
    }, 800);
}
