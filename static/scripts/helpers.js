// Additional helper scripts

async function copyGameLinkToClipboard() {
  const copyUrl = window.location.href;
  console.log("URL is `" + copyUrl + "`.");
  await navigator.clipboard.writeText(copyUrl);
  // set the value of a hidden object to allow the
  // "copied to clipboard" message to appear
  changeCopySuccessVisibility('visible');
  setTimeout(changeCopySuccessVisibility, 5000, 'hidden');
  return 0
}

function changeCopySuccessVisibility(viz) {
  var success = document.getElementById('success-message');
  success.style.visibility = viz;
}
