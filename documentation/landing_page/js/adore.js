new ClipboardJS('.btn');

$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip({ show: null });
});

function show(shown) {
    ['about', 'scenario', 'quickstart', 'documentation', 'contribute', 'sponsors', 'contact'].forEach(function (id) {
        document.getElementById(id).style.display = 'none';
    });
    document.getElementById(shown).style.display = shown === 'about' || shown === 'scenario' ? 'flex' : 'block';
    return false;
}
