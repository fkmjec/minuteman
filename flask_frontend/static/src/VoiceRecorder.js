import { create, ConverterType } from "@alexanderolsen/libsamplerate-js";


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

class VoiceRecorder extends AudioWorkletProcessor {
    constructor(options) {
        super();


        this.savedVoiceData = [];
        this.converter = null;
        if (options && options.processorOptions) {
            this.sampleRate = options.processorOptions.sampleRate;
            this.targetSampleRate = options.processorOptions.targetSampleRate;
            this.sentChunkLen = options.processorOptions.sentChunkLen;
            // this.maxSavedLen = options.processorOptions.maxSavedLen;
        } else {
            throw new Error("options must be provided to Voice Recorder");
        }
        this.createConverter()

        this.port.onmessage = (e) => {
            if (e == "stop") {
                this.stopRecording();
            }
        }

        this.utteranceStart = new Date();
        this.recording = true;
    }

    decimate(data) {
        return this.converter.full(data);
    }
    
    async createConverter () {
        console.info("creating converter");
        let converterType = ConverterType.SRC_SINC_FASTEST;
        let nChannels = 1;
        this.converter = await create(nChannels, this.sampleRate, this.targetSampleRate, { converterType: converterType });
        console.info("created converter");
    }

    // data is a Float32Array
    storeFloats(data) {
        const decimated = this.decimate(data);
        this.savedVoiceData.push(decimated);
    }

    stopRecording() {
        this.recording = false;
        this.converter.destroy();
        // TODO: maybe clean up all the buffers?
    }

    clearBuffer() {
        this.savedVoiceData = [];
    }


    shouldSend() {
        const totalLen = this.savedVoiceData.reduce((acc, chunk) => acc + chunk.length, 0);
        const lenInSec = totalLen / (this.targetSampleRate);
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

        if (!this.converter) {
            // wait with recorder until converter is ready
            return this.recording;
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
