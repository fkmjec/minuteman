function mergeChunks(chunks) {
    const totalLen = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    const merged = new Float32Array(totalLen);
    let offset = 0;
    for (const chunk of chunks) {
        merged.set(chunk, offset);
        offset += chunk.length;
    }
    return merged;
}

function decimate(data, factor) {
    // TODO: this is just a placeholder, we need to get a library for this
    const decimated = new Float32Array(Math.floor(data.length / factor));
    for (let i = 0; i < decimated.length; i++) {
        const index = Math.floor(i * factor);
        decimated[i] = data[i * factor];
    }
    return decimated;
}

class VoiceRecorder extends AudioWorkletProcessor {
    constructor(options) {
        super();
        this.savedVoiceData = [];
        console.info(options);
        if (options && options.processorOptions) {
            this.sampleRate = options.processorOptions.sampleRate;
            this.targetSampleRate = options.processorOptions.targetSampleRate;
            this.sentChunkLen = options.processorOptions.sentChunkLen;
            // this.maxSavedLen = options.processorOptions.maxSavedLen;
        } else {
            throw new Error("options must be provided to Voice Recorder");
        }

        this.decimationFactor = this.sampleRate / this.targetSampleRate;
        console.info(this.decimationFactor);
        this.utteranceStart = new Date();
        this.recording = true;
    }

    // data is a Float32Array
    storeFloats(data) {
        const decimated = decimate(data, this.decimationFactor);
        this.savedVoiceData.push(decimated);
    }

    stopRecording() {
        this.recording = false;
        // TODO: maybe clean up all the buffers?
        // this means that the VoiceRecorder will be removed
    }

    clearBuffer(position) {
        this.savedVoiceData = [];
    }


    shouldSend() {
        if (this.savedVoiceData.length === 0) {
            return false;
        }
        const chunkLen = this.savedVoiceData[0].length;
        const totalLen = this.savedVoiceData.length * chunkLen;
        const lenInSec = totalLen / (this.sampleRate /  this.decimationFactor);
        return lenInSec >= this.sentChunkLen;
    }
  
    process(inputList, outputList, parameters) {
        // Using the inputs (or not, as needed),
        // write the output into each of the outputs
        // …
        // we assume the input only has one channel (is mono)
        if (inputList.length !== 1) {
            throw new Error("InputList should contain at least one input float array.");
        }
        let relevantData = inputList[0][0];
        if (relevantData) {
            this.storeFloats(relevantData);
            if (this.shouldSend()) {
                let merged = mergeChunks(this.savedVoiceData);
                this.port.postMessage({ type: "voiceData", data: merged });
                this.clearBuffer();
            }
        }
        // if process returns false, the node will be removed
        return this.recording;
    }
}

registerProcessor("VoiceRecorder", VoiceRecorder);
