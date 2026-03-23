import glob
import os

js_code = """
<script>
document.addEventListener("DOMContentLoaded", () => {
    const navMapping = {
        'Dashboard': '/',
        'Calendar': '/calendar',
        'Minutes': '/minutes',
        'Meeting Minutes': '/minutes',
        'Command Center': '/command',
        'Voice Command': '/command'
    };
    
    // Find all potential navigation items
    const elements = document.querySelectorAll('a, div, span, li');
    
    elements.forEach(el => {
        const text = el.textContent.trim();
        // Check if the element text exactly matches one of our navigation keys
        // or if it's a known nav container, but exact match is safer if we just look at children
        for (const [key, path] of Object.entries(navMapping)) {
            if (text === key || text === key + " " || el.innerText.trim() === key) {
                // To avoid replacing things too broadly, only target elements that look like nav links
                // like if they have 'cursor-pointer' or are an 'a' tag, or their parent is a nav
                if (el.tagName === 'A' || el.classList.contains('cursor-pointer') || el.closest('nav')) {
                    // find closest clickable parent
                    const clickable = el.closest('a') || el.closest('.cursor-pointer') || el;
                    
                    // Attach click event
                    clickable.addEventListener('click', (e) => {
                        e.preventDefault();
                        window.location.href = path;
                    });
                }
            }
        }
    });
});
</script>
"""

for filepath in glob.glob('/root/casperAI/frontend/src/screens/*.html'):
    with open(filepath, 'r') as f:
        content = f.read()
    
    if "navMapping" not in content:
        content = content.replace('</body>', js_code + '\n</body>')
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Injected nav script into {filepath}")
