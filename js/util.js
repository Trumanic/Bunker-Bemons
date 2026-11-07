import { flagCodes } from './countries.js';

// https://stackoverflow.com/questions/3452546/how-do-i-get-the-youtube-video-id-from-a-url
export function getYoutubeIdFromUrl(url) {
    return url.match(
        /.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*/,
    )?.[1] ?? '';
}

export function embed(video) {
    return `https://www.youtube.com/embed/${getYoutubeIdFromUrl(video)}`;
}


export function localize(num) {
    return num.toLocaleString(undefined, {
        maximumFractionDigits: 1,
    });
}


export function getThumbnailFromId(id) {
    return [
        `https://img.youtube.com/vi/${id}/maxresdefault.jpg`,
        `https://img.youtube.com/vi/${id}/sddefault.jpg`,
        `https://img.youtube.com/vi/${id}/hqdefault.jpg`,
        `https://img.youtube.com/vi/${id}/mqdefault.jpg`,
    ];
}
// https://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
export function shuffle(array) {
    let currentIndex = array.length, randomIndex;

    // While there remain elements to shuffle.
    while (currentIndex != 0) {
        // Pick a remaining element.
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        // And swap it with the current element.
        [array[currentIndex], array[randomIndex]] = [
            array[randomIndex],
            array[currentIndex],
        ];
    }

    return array;
}

export function formatDate(dateStr) {
    if (!dateStr) return '';

    const value = String(dateStr).trim();

    // Already D/M/YYYY
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(value)) {
        return value;
    }

    // Support old YYYY-MM-DD dates just in case
    const match = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);

    if (match) {
        const [, year, month, day] = match;
        return `${Number(day)}/${Number(month)}/${year}`;
    }

    return value;
}

export function parseDate(dateStr) {
    if (!dateStr) return null;

    const value = String(dateStr).trim();

    let year, month, day;

    let match = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);

    if (match) {
        [, day, month, year] = match.map(Number);
    } else {
        match = value.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);

        if (!match) return null;

        [, year, month, day] = match.map(Number);
    }

    const date = new Date(year, month - 1, day);

    if (
        date.getFullYear() !== year ||
        date.getMonth() !== month - 1 ||
        date.getDate() !== day
    ) {
        return null;
    }

    return date.getTime();
}

// ---- Countries ----
const customCountryNames = {
    'gb-eng': 'England',
    'gb-sct': 'Scotland',
    'gb-wls': 'Wales',
    'gb-nir': 'Northern Ireland',
    eu: 'European Union',
    un: 'United Nations',
    xk: 'Kosovo',
    'es-ct': 'Catalonia',
    'es-ga': 'Galicia',
    'es-pv': 'Basque Country',
};

const regionNames =
    typeof Intl !== 'undefined' && Intl.DisplayNames
        ? new Intl.DisplayNames(['en'], { type: 'region' })
        : null;

/**
 * Cleans up a country code from players.json ("ma", " MA ", "gb-eng" ...).
 * Returns '' when it isn't a country that has a flag.
 */
export function normalizeCountry(code) {
    const c = String(code ?? '').trim().toLowerCase();
    return flagCodes.has(c) ? c : '';
}

/**
 * Full country name for a code, e.g. "ma" -> "Morocco"
 */
export function countryName(code) {
    const c = normalizeCountry(code);
    if (!c) {
        return '';
    }
    if (customCountryNames[c]) {
        return customCountryNames[c];
    }
    try {
        return regionNames?.of(c.toUpperCase()) ?? c.toUpperCase();
    } catch {
        return c.toUpperCase();
    }
}
