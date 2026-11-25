/* Return focus to the panel's trigger after it closes.
 *
 * Closing the offcanvas unmounts it, and the browser drops focus to <body> -
 * so the next Tab restarts at the top of the document instead of continuing
 * from where the user was. The trigger is the button they pressed to open it.
 */
document.addEventListener('click', function (event) {
  var closer = event.target.closest('#input_sidebar .btn-close');
  if (!closer) return;

  // Wait for the offcanvas transition and the React unmount to finish.
  setTimeout(function () {
    var toggle = document.getElementById('input_sidebar_toggle');
    if (toggle && toggle.offsetParent !== null) {
      toggle.focus();
    }
  }, 350);
});
