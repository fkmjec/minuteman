class VoiceRecorder extends AudioWorkletProcessor {
    constructor() {
        super();
        // the saved chunks of floats, a rolling buffer that is always at least a second long;
        // if the last second contains speech, it is extended, else it is cut down to the last second 
        this.savedVoiceData = [];
        this.i = 0;
    }

    storeFloats(inputList) {

    }
  
    process(inputList, outputList, parameters) {
        // Using the inputs (or not, as needed),
        // write the output into each of the outputs
        // …
        // console.log("MediaChunkRecorder process called!");
        if (this.i % 10000 == 0) {
            console.info(inputList);
        }
        this.i += 1;
        return true;
    }
}
  
registerProcessor("VoiceRecorder", VoiceRecorder);
