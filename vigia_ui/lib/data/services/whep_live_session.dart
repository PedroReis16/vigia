import 'dart:async';
import 'dart:math' as math;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';

enum WhepLiveStatus { connecting, playing, error }

/// Manages a receive-only WHEP session against MediaMTX.
///
/// Dispose closes the peer connection only — callers must not send
/// STOP_STREAMING here (MediaMTX runOnUnDemand owns that).
class WhepLiveSession extends ChangeNotifier {
  WhepLiveSession({required this.whepUrl, Dio? dio})
    : _dio = dio ?? Dio();

  final String whepUrl;
  final Dio _dio;

  final RTCVideoRenderer renderer = RTCVideoRenderer();

  WhepLiveStatus status = WhepLiveStatus.connecting;
  String? errorMessage;
  bool isPaused = false;

  RTCPeerConnection? _peerConnection;
  MediaStream? _remoteStream;
  bool _disposed = false;
  bool _rendererReady = false;
  int _connectGeneration = 0;

  Future<void> initialize() async {
    if (_rendererReady) return;
    await renderer.initialize();
    _rendererReady = true;
  }

  void beginConnecting() {
    if (_disposed) return;
    status = WhepLiveStatus.connecting;
    errorMessage = null;
    isPaused = false;
    notifyListeners();
  }

  void markError(Object error) {
    if (_disposed) return;
    status = WhepLiveStatus.error;
    errorMessage = error.toString();
    notifyListeners();
  }

  Future<void> connect({
    int maxAttempts = 24,
    Duration initialDelay = const Duration(milliseconds: 500),
    Duration maxDelay = const Duration(seconds: 5),
  }) async {
    if (_disposed) return;

    final generation = ++_connectGeneration;
    beginConnecting();

    var delay = initialDelay;
    Object? lastError;

    for (var attempt = 0; attempt < maxAttempts; attempt++) {
      if (_disposed || generation != _connectGeneration) return;

      try {
        await _negotiate();
        if (_disposed || generation != _connectGeneration) return;
        status = WhepLiveStatus.playing;
        errorMessage = null;
        notifyListeners();
        return;
      } catch (e) {
        lastError = e;
        await _teardownPeer();
        if (_disposed || generation != _connectGeneration) return;
        if (attempt == maxAttempts - 1) break;
        await Future<void>.delayed(delay);
        final nextMs = math.min(
          delay.inMilliseconds * 2,
          maxDelay.inMilliseconds,
        );
        delay = Duration(milliseconds: nextMs);
      }
    }

    if (_disposed || generation != _connectGeneration) return;
    markError(lastError ?? 'Failed to connect to live stream');
  }

  void togglePause() {
    final stream = _remoteStream;
    if (stream == null || status != WhepLiveStatus.playing) return;

    isPaused = !isPaused;
    for (final track in stream.getVideoTracks()) {
      track.enabled = !isPaused;
    }
    for (final track in stream.getAudioTracks()) {
      track.enabled = !isPaused;
    }
    notifyListeners();
  }

  Future<void> _negotiate() async {
    await initialize();

    final pc = await createPeerConnection({
      'sdpSemantics': 'unified-plan',
      'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'},
      ],
    });
    _peerConnection = pc;

    pc.onTrack = (RTCTrackEvent event) {
      if (_disposed) return;
      if (event.streams.isEmpty) return;
      _remoteStream = event.streams.first;
      renderer.srcObject = _remoteStream;
      notifyListeners();
    };

    await pc.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeVideo,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );
    await pc.addTransceiver(
      kind: RTCRtpMediaType.RTCRtpMediaTypeAudio,
      init: RTCRtpTransceiverInit(direction: TransceiverDirection.RecvOnly),
    );

    final offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await _waitForIceGathering(pc);

    final local = await pc.getLocalDescription();
    final sdp = local?.sdp;
    if (sdp == null || sdp.isEmpty) {
      throw Exception('Empty local SDP offer');
    }

    final response = await _dio.post<String>(
      whepUrl,
      data: sdp,
      options: Options(
        contentType: 'application/sdp',
        responseType: ResponseType.plain,
        headers: {'Accept': 'application/sdp'},
        validateStatus: (status) => status != null && status < 500,
      ),
    );

    final code = response.statusCode ?? 0;
    if (code != 200 && code != 201) {
      throw Exception('WHEP negotiate failed ($code)');
    }

    final answerSdp = response.data;
    if (answerSdp == null || answerSdp.isEmpty) {
      throw Exception('Empty WHEP SDP answer');
    }

    await pc.setRemoteDescription(
      RTCSessionDescription(answerSdp, 'answer'),
    );
  }

  Future<void> _waitForIceGathering(RTCPeerConnection pc) async {
    if (pc.iceGatheringState ==
        RTCIceGatheringState.RTCIceGatheringStateComplete) {
      return;
    }

    final completer = Completer<void>();
    pc.onIceGatheringState = (RTCIceGatheringState state) {
      if (state == RTCIceGatheringState.RTCIceGatheringStateComplete &&
          !completer.isCompleted) {
        completer.complete();
      }
    };

    await completer.future.timeout(
      const Duration(seconds: 8),
      onTimeout: () {},
    );
  }

  Future<void> _teardownPeer() async {
    final stream = _remoteStream;
    _remoteStream = null;
    renderer.srcObject = null;

    if (stream != null) {
      for (final track in stream.getTracks()) {
        await track.stop();
      }
      await stream.dispose();
    }

    final pc = _peerConnection;
    _peerConnection = null;
    if (pc != null) {
      await pc.close();
      await pc.dispose();
    }
  }

  /// Closes the peer connection and renderer. Does not send STOP_STREAMING.
  Future<void> close() async {
    if (_disposed) return;
    _disposed = true;
    _connectGeneration++;
    await _teardownPeer();
    if (_rendererReady) {
      await renderer.dispose();
      _rendererReady = false;
    }
    dispose();
  }
}
