import { NonRealTimeVAD } from "@ricky0123/vad-web";

// class VoiceRecordBuffer {
//     constructor(maxLenInSeconds, sampleRate, keepLastSeconds) {
//         this.capacity = maxLenInSeconds * sampleRate;
//         this.array = new Float32Array(this.capacity);
//         this.size = 0;
//         if (keepLastSeconds > maxLenInSeconds) {
//             throw new Error("keepLastSeconds must be smaller than maxLenInSeconds");
//         }
//         this.keepLastSeconds = keepLastSeconds;
//     }

//     // if the buffer cannot contain all the elements,
//     // this function returns false and does not add anything. The caller then must flush the buffer and call push again
//     // if the push was successful, the function returns true
//     push(newValues) {
//         const elements = newValues.length;
//         if (this.size + elements > this.array.size) {
//             return false;
//         }

//         for (let i = 0; i < elements; i++) {
//             const currentPos = this.size + i;
//             this.array[currentPos] = newValues[i];
//         }
//         size += elements;
//         return true;
//     }

//     getContents() {
        
//     }

//     flush () {

//     }
// }

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
        console.info(options);
        if (options && options.processorOptions) {
            this.sampleRate = options.processorOptions.sampleRate;
            this.voiceCheckingLen = options.processorOptions.voiceCheckingLen;
            this.maxSavedLen = options.processorOptions.maxSavedLen;
        } else {
            throw new Error("options must be provided to Voice Recorder");
        }

        // this.sampleRate = sampleRate;
        this.i = 0;
        this.utteranceStart = new Date();
        this.recording = true;
    }

    setSampleRate(sampleRate) {
        this.sampleRate = sampleRate;
    }

    // data is a Float32Array
    storeFloats(data) {
        this.savedVoiceData.push(data);
    }

    stopRecording() {
        this.recording = false;
        // TODO: maybe clean up all the buffers?
    }

    async containsSpeech(voiceDataBuffer) {
        const merged = mergeChunks(voiceDataBuffer);
        if (!this.VAD) {
            this.VAD = await NonRealTimeVAD.new({});
        }
        let hasSpeech = false;
        for await (const {audio, start, end} of this.VAD.run(merged, this.sampleRate)) {
            hasSpeech = true;
        }
        return hasSpeech;
    }

    flushBufferToPosition(position) {
        this.savedVoiceData = oldData.slice(position);
    }

    // checks whether speech should be uploaded and if it is, it sends the data to the node
    async checkVAD(currentBufferLen) {
        let shouldSend = false;
        
        const chunkLen = this.savedVoiceData[0].length;
        const savedDuration = currentBufferLen * chunkLen / this.sampleRate;
        if (savedDuration > this.maxSavedLen) {
            shouldSend = true;
        } else {
            const relevantChunkStart = currentBufferLen - this.voiceCheckingLen * this.sampleRate / chunkLen;
            if (relevantChunkStart < 0) {
                throw new Error("started voice checking on a segment shorter than the voice checking length");
            }
            const relevantChunks = this.savedVoiceData.slice(relevantChunkStart, currentBufferLen);
            shouldSend = await this.containsSpeech(relevantChunks);
        }
        if (shouldSend) {
            this.port.postMessage({ type: "voiceData", data: this.savedVoiceData.slice(0, currentBufferLen) });
            // we hope this happens fast enough so that we do not lose any data here.
            this.flushBufferToPosition(currentBufferLen);
        }
    }

    shouldCheckVAD() {
        if (this.savedVoiceData.length === 0) {
            return false;
        }
        const chunkLen = this.savedVoiceData[0].length;
        const totalLen = this.savedVoiceData.length * chunkLen;
        const lenInSec = totalLen / this.sampleRate;
        // console.info(lenInSec);
        // console.info(this.sampleRate);
        return lenInSec >= this.voiceCheckingLen;
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
            console.info("lol")
            if (this.shouldCheckVAD()) {
                // runs asynchronously and if the segment is not speech, it will send 
                // the data recorded in the past to the server
                this.checkVAD(this.savedVoiceData.length);
            }
        }
        // if process returns false, the node will be removed
        return this.recording;
    }
}

registerProcessor("VoiceRecorder", VoiceRecorder);
