import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image/image.dart' as img;
import 'package:flutter_tts/flutter_tts.dart'; // Import TTS package
import 'services/api_service.dart'; // Import your API service

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({Key? key}) : super(key: key);

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  final ImagePicker _picker = ImagePicker();
  String _code = '';
  final ApiService _apiService = ApiService();
  bool _isProcessing = false;
  final FlutterTts _flutterTts = FlutterTts(); // Initialize TTS instance

  Future<void> _captureAndProcessImage() async {
    if (_isProcessing) return; // Prevent re-entry if already processing
    _isProcessing = true;

    setState(() {
      _code = 'Processing...';
    });

    try {
      // Capture image using the device's camera
      final XFile? image = await _picker.pickImage(source: ImageSource.camera);

      if (image == null) {
        setState(() {
          _code = "No image captured";
        });
        _isProcessing = false;
        return;
      }

      // Read the image bytes
      final bytes = await image.readAsBytes();
      // Decode the image for further processing
      final bitmapImage = img.decodeImage(bytes);

      if (bitmapImage != null) {
        // Convert image to JPEG format for uploading
        final jpegBytes = img.encodeJpg(bitmapImage);

        // Send image to the server and await the response
        final result =
            await _apiService.processImage(Uint8List.fromList(jpegBytes));

        setState(() {
          _code = result; // Display server response
        });

        // Speak the result using TTS
        await _speakText(result);
      } else {
        setState(() {
          _code = "Error processing image";
        });
      }
    } catch (e) {
      setState(() {
        _code = "Capture failed: $e";
      });
    } finally {
      _isProcessing = false;
    }
  }

  // Function to speak text using TTS
  Future<void> _speakText(String text) async {
    text = text
        .replaceAll('/', ' divided by ')
        .replaceAll('*', ' multiplied by ')
        .replaceAll('+', ' plus ')
        .replaceAll('-', ' minus ')
        .replaceAll('=', ' equals ');

    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setPitch(1.0);
    await _flutterTts.speak(text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Visual Programming App'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text('Captured Code:'),
            Text(
              _code,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _captureAndProcessImage,
              child: Text('Capture Image'),
            ),
          ],
        ),
      ),
    );
  }
}
