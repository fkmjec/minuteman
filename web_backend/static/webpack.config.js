const CopyPlugin = require("copy-webpack-plugin")


module.exports = [
{
  name: "main",
  entry: "./src/index.js",
  target: "web",
  output: { 
    filename: "main.js",
  }
},
{
  name: "VoiceRecorder",
  entry: "./src/VoiceRecorder.js",
  target: "web",
  mode: "development",
  output: {
    filename: "VoiceRecorder.js",
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        {
          from: "node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js",
          to: "[name][ext]",
        },
        {
          from: "node_modules/@ricky0123/vad-web/dist/*.onnx",
          to: "[name][ext]",
        },
        { from: "node_modules/onnxruntime-web/dist/*.wasm", to: "[name][ext]" },
      ],
    }),
  ],
}
,]