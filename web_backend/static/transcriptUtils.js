export class Utterance {
    constructor (start, author, utterance) {
        this.author = author;
        this.start = start;
        this.utterance = utterance;
    }

    toString() {
        return `${this.author}: ${this.utterance}`;
    }
}

export class Transcript {
    constructor () {
        this.utterances = [];
    }

    addUtterance(utterance) {
        this.utterances.push(utterance);
        // FIXME: is this the best order?
        // it will be rendered live, we do not need to care about the cost of sorting
        this.utterances.sort((a, b) => a.start - b.start);
    }

    toString() {
        return this.utterances.map(utterance => utterance.toString()).join('\n');
    }
}

export default { Utterance, Transcript };