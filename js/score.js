/**
 * Numbers of decimal digits to round to
 */
const scale = 2;

/**
 * Points awarded for the #1 and last-ranked level on the list.
 * Every level in between is spaced out evenly (linear).
 */
export const MAX_POINTS = 100;
export const MIN_POINTS = 1;

/**
 * Calculate the points a level is worth based on its position on the list.
 * Every record counts as a 100% completion, so there is no percentage.
 * @param {Number} rank Position on the list (1 = hardest)
 * @param {Number} total Total number of levels on the list
 * @returns {Number}
 */
export function score(rank, total) {
    if (total <= 1) {
        return MAX_POINTS;
    }

    const step = (MAX_POINTS - MIN_POINTS) / (total - 1);
    return round(MAX_POINTS - (rank - 1) * step);
}

export function round(num) {
    if (!('' + num).includes('e')) {
        return +(Math.round(num + 'e+' + scale) + 'e-' + scale);
    } else {
        var arr = ('' + num).split('e');
        var sig = '';
        if (+arr[1] + scale > 0) {
            sig = '+';
        }
        return +(
            Math.round(+arr[0] + 'e' + sig + (+arr[1] + scale)) +
            'e-' +
            scale
        );
    }
}
