export function createNode(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.firstElementChild;
}