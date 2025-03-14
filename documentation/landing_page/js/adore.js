new ClipboardJS('.btn');

$(document)
$(document).ready(function() {
  // Initialize tooltips
  $('[data-toggle="tooltip"]').tooltip({show: null});
});

function show(shown) {
  document.getElementById('about').style.display='none';
  document.getElementById('getting-started').style.display='none';
  document.getElementById('contribute').style.display='none';
  document.getElementById('sponsors').style.display='none';
  document.getElementById('contact').style.display='none';
  document.getElementById(shown).style.display='block';
  return false;
}
