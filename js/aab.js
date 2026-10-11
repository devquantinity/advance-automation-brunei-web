/* Advance Automation - the site's own script (the template's scripts are untouched apart from the note at the top of
   site.schunk.ef3d838b12b5ed87.js).

   Home, "Our services": the six cards show their picture and open one by one while the page scrolls.  A card opens
   (picture fades out, plus turns into a minus - css/aab.css, .aab-open) once its middle has scrolled above a line on
   the screen.  In a row the line is a little higher for each next card, so a row opens left to right and then the next
   row follows; on a phone every card is its own row.  Scrolling back up closes them again in reverse order. */
(function () {
    var cards = Array.prototype.slice.call(document.querySelectorAll('.fda-solutions-v4-item'));
    if (!cards.length) return;

    var FIRST = 0.72; // first card of a row: its middle passes 72% of the screen height
    var STEP = 0.11; // each next card of the row: 11% of the screen height higher
    var waiting = false;

    function update() {
        waiting = false;
        var screen = window.innerHeight || document.documentElement.clientHeight;
        var rowTop = null;
        var column = 0;
        for (var i = 0; i < cards.length; i++) {
            var box = cards[i].getBoundingClientRect();
            if (rowTop === null || Math.abs(box.top - rowTop) > 2) {
                rowTop = box.top;
                column = 0;
            } else {
                column += 1;
            }
            var line = screen * (FIRST - STEP * column);
            cards[i].classList.toggle('aab-open', box.top + box.height / 2 < line);
        }
    }

    function later() {
        if (!waiting) {
            waiting = true;
            window.requestAnimationFrame(update);
        }
    }

    window.addEventListener('scroll', later, { passive: true });
    window.addEventListener('resize', later);
    window.addEventListener('load', later);
    // the cards slide into place when they come into view; check again while that happens without scrolling
    window.setInterval(later, 400);
    later();
})();
