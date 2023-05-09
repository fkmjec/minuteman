class VoiceRecorder extends AudioWorkletProcessor {
    constructor() {
        super();
    }
  
    process(inputList, outputList, parameters) {
        // Using the inputs (or not, as needed),
        // write the output into each of the outputs
        // …
        console.info("MediaChunkRecorder process called!");
        console.info(inputList);
        return true;
    }
}
  
registerProcessor("VoiceRecorder", VoiceRecorder);
