const fs = require('fs');

const path = require('path');

const js_code = `
<script>
document.addEventListener("DOMContentLoaded", () => {
    const navMapping = {
        'Dashboard': '/',
        'Calendar': '/calendar',
        'Minutes': '/minutes',
        'Command Center': '/command'
    };
    
    document.querySelectorAll('a, div, span').forEach(el => {
        const text = el.innerText ? el.innerText.trim() : el.textContent.trim();
        for (const [key, path] of Object.entries(navMapping)) {
            // Find elements containing the exact text as their only content
            if (text === key && el.children.length === 0) {
                const clickable = el.closest('a') || el.closest('.cursor-pointer') || el.closest('.group');
                if (clickable) {
                    clickable.addEventListener('click', (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        window.location.href = path;
                    });
                }
            }
        }
    });
});
</script>
`;

const dir = '/root/casperAI/frontend/src/screens/';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));

files.forEach(file => {
    const filePath = path.join(dir, file);
    let content = fs.readFileSync(filePath, 'utf8');
    if (!content.includes('navMapping')) {
        content = content.replace('</body>', js_code + '\n</body>');
        fs.writeFileSync(filePath, content);
        console.log('Injected into', file);
    }
});
