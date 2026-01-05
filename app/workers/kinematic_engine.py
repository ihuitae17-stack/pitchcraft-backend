"""
PitchCraft Kinematic Analysis Engine

프론트엔드의 키네마틱 분석 로직을 Python으로 포팅한 모듈.
각속도 계산, 키네마틱 시퀀스 분석, 에너지 효율 점수 산출.
"""
import math
import tempfile
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import cv2
import numpy as np
import mediapipe as mp


@dataclass
class PoseFrame:
    """단일 프레임의 포즈 데이터"""
    time: float
    keypoints: Dict[str, Dict[str, float]]


class KinematicEngine:
    """투구 메커니즘 분석 엔진"""
    
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # MediaPipe 관절 이름 매핑
        self.landmark_names = {
            0: 'nose',
            11: 'left_shoulder', 12: 'right_shoulder',
            13: 'left_elbow', 14: 'right_elbow',
            15: 'left_wrist', 16: 'right_wrist',
            23: 'left_hip', 24: 'right_hip',
        }
    
    def extract_poses_from_video(self, video_path: str, sample_fps: float = 10.0) -> List[PoseFrame]:
        """영상에서 포즈 추출"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / original_fps if original_fps > 0 else 0
        
        # 샘플링 간격 계산
        frame_interval = max(1, int(original_fps / sample_fps))
        
        poses = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % frame_interval == 0:
                current_time = frame_idx / original_fps
                
                # BGR -> RGB 변환
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb_frame)
                
                if results.pose_landmarks:
                    keypoints = {}
                    for idx, name in self.landmark_names.items():
                        lm = results.pose_landmarks.landmark[idx]
                        keypoints[name] = {
                            'x': lm.x,
                            'y': lm.y,
                            'z': lm.z,
                            'score': lm.visibility
                        }
                    poses.append(PoseFrame(time=current_time, keypoints=keypoints))
            
            frame_idx += 1
        
        cap.release()
        return poses
    
    def _get_midpoint(self, p1: Dict, p2: Dict) -> Dict:
        """두 점의 중점 계산"""
        return {
            'x': (p1['x'] + p2['x']) / 2,
            'y': (p1['y'] + p2['y']) / 2,
            'score': min(p1.get('score', 1), p2.get('score', 1))
        }
    
    def _calculate_angle(self, a: Dict, b: Dict, c: Dict) -> Optional[float]:
        """세 점으로 각도 계산 (라디안)"""
        if not all([a, b, c]):
            return None
        if any(p.get('score', 0) < 0.3 for p in [a, b, c]):
            return None
        
        angle1 = math.atan2(c['y'] - b['y'], c['x'] - b['x'])
        angle2 = math.atan2(a['y'] - b['y'], a['x'] - b['x'])
        return angle1 - angle2
    
    def calculate_angular_velocity(self, poses: List[PoseFrame], fps: float = 10.0) -> Dict[str, List[float]]:
        """분절별 각속도 계산"""
        delta_t = 1.0 / fps
        
        # 각 분절의 각도 시계열
        angles = {'pelvis': [], 'torso': [], 'upperArm': [], 'forearm': []}
        
        for pose in poses:
            kp = pose.keypoints
            
            # 가상 포인트 생성
            left_hip = kp.get('left_hip')
            right_hip = kp.get('right_hip')
            left_shoulder = kp.get('left_shoulder')
            right_shoulder = kp.get('right_shoulder')
            nose = kp.get('nose')
            right_elbow = kp.get('right_elbow')
            right_wrist = kp.get('right_wrist')
            
            mid_hip = self._get_midpoint(left_hip, right_hip) if left_hip and right_hip else None
            mid_shoulder = self._get_midpoint(left_shoulder, right_shoulder) if left_shoulder and right_shoulder else None
            
            # 골반 각도
            angles['pelvis'].append(self._calculate_angle(left_hip, mid_hip, right_hip) if mid_hip else None)
            
            # 몸통 각도
            angles['torso'].append(self._calculate_angle(mid_hip, mid_shoulder, nose) if mid_hip and mid_shoulder and nose else None)
            
            # 상박 각도
            angles['upperArm'].append(self._calculate_angle(right_shoulder, right_elbow, right_wrist) if all([right_shoulder, right_elbow, right_wrist]) else None)
            
            # 전완 각도 (연장선)
            if right_elbow and right_wrist:
                extended = {
                    'x': right_wrist['x'] + (right_wrist['x'] - right_elbow['x']),
                    'y': right_wrist['y'] + (right_wrist['y'] - right_elbow['y']),
                    'score': min(right_elbow.get('score', 1), right_wrist.get('score', 1))
                }
                angles['forearm'].append(self._calculate_angle(right_elbow, right_wrist, extended))
            else:
                angles['forearm'].append(None)
        
        # 각속도 계산 (미분)
        velocities = {}
        for segment, angle_list in angles.items():
            vels = [0.0]  # 첫 프레임
            for i in range(1, len(angle_list)):
                if angle_list[i] is not None and angle_list[i-1] is not None:
                    delta = angle_list[i] - angle_list[i-1]
                    # 각도 불연속 처리
                    if delta > math.pi:
                        delta -= 2 * math.pi
                    if delta < -math.pi:
                        delta += 2 * math.pi
                    # deg/s 변환
                    vels.append(abs(delta / delta_t) * (180 / math.pi))
                else:
                    vels.append(0.0)
            
            # 이동 평균 필터 (윈도우 3)
            velocities[segment] = self._moving_average(vels, 3)
        
        return velocities
    
    def _moving_average(self, data: List[float], window: int = 3) -> List[float]:
        """이동 평균 필터"""
        result = []
        half = window // 2
        for i in range(len(data)):
            start = max(0, i - half)
            end = min(len(data), i + half + 1)
            result.append(sum(data[start:end]) / (end - start))
        return result
    
    def analyze_kinematic_sequence(self, velocities: Dict[str, List[float]], fps: float = 10.0) -> Dict[str, Any]:
        """키네마틱 시퀀스 분석"""
        segments = ['pelvis', 'torso', 'upperArm', 'forearm']
        peak_times = {}
        peak_values = {}
        
        for segment in segments:
            data = velocities.get(segment, [])
            if not data:
                peak_times[segment] = 0.0
                peak_values[segment] = 0.0
                continue
            
            max_idx = max(range(len(data)), key=lambda i: data[i])
            peak_times[segment] = max_idx / fps
            peak_values[segment] = data[max_idx]
        
        # 시간 Gap 계산
        gaps = {
            'pelvis_to_torso': peak_times['torso'] - peak_times['pelvis'],
            'torso_to_arm': peak_times['upperArm'] - peak_times['torso'],
            'arm_to_hand': peak_times['forearm'] - peak_times['upperArm'],
        }
        
        # 위반 검출
        violations = []
        if peak_times['torso'] < peak_times['pelvis']:
            violations.append('EARLY_TORSO')
        if peak_times['upperArm'] < peak_times['torso']:
            violations.append('EARLY_ARM_ACTION')
        if peak_times['forearm'] < peak_times['upperArm']:
            violations.append('EARLY_HAND')
        
        return {
            'peak_times': peak_times,
            'peak_values': peak_values,
            'gaps': gaps,
            'violations': violations,
            'is_valid_sequence': len(violations) == 0
        }
    
    def calculate_efficiency_score(self, sequence_result: Dict, velocities: Dict) -> Dict[str, Any]:
        """에너지 전달 효율 점수 산출"""
        # 1. 시퀀스 순서 준수 (40점)
        violation_count = len(sequence_result.get('violations', []))
        if violation_count == 0:
            sequence_score = 40
        elif violation_count == 1:
            sequence_score = 25
        else:
            sequence_score = 10
        
        # 2. Gap 균일성 (30점)
        gaps = list(sequence_result.get('gaps', {}).values())
        valid_gaps = [g for g in gaps if g is not None and not math.isnan(g) and not math.isinf(g)]
        if valid_gaps and len(valid_gaps) > 1:
            mean = sum(valid_gaps) / len(valid_gaps)
            if mean > 0:
                variance = sum((g - mean) ** 2 for g in valid_gaps) / len(valid_gaps)
                std = math.sqrt(variance)
                uniformity_score = round(30 * max(0, 1 - std / abs(mean)))
            else:
                uniformity_score = 15
        else:
            uniformity_score = 15
        
        # 3. 피크 증폭 비율 (30점)
        peak_values = sequence_result.get('peak_values', {})
        pelvis_peak = peak_values.get('pelvis', 1)
        forearm_peak = peak_values.get('forearm', 0)
        ratio = forearm_peak / max(pelvis_peak, 1)
        
        if 3.0 <= ratio <= 4.0:
            amplification_score = 30
        elif (2.5 <= ratio < 3.0) or (4.0 < ratio <= 4.5):
            amplification_score = 20
        else:
            amplification_score = 10
        
        total = sequence_score + uniformity_score + amplification_score
        
        # 등급 산출
        if total >= 85:
            grade = 'A+'
        elif total >= 75:
            grade = 'A'
        elif total >= 65:
            grade = 'B+'
        elif total >= 55:
            grade = 'B'
        elif total >= 45:
            grade = 'C+'
        else:
            grade = 'C'
        
        return {
            'total_score': total,
            'grade': grade,
            'breakdown': {
                'sequence_score': sequence_score,
                'uniformity_score': uniformity_score,
                'amplification_score': amplification_score
            }
        }
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """전체 분석 파이프라인 실행"""
        # 1. 포즈 추출
        poses = self.extract_poses_from_video(video_path, sample_fps=10.0)
        
        if len(poses) < 5:
            return {
                'error': 'Not enough frames detected',
                'frame_count': len(poses)
            }
        
        # 2. 각속도 계산
        velocities = self.calculate_angular_velocity(poses, fps=10.0)
        
        # 3. 키네마틱 시퀀스 분석
        sequence = self.analyze_kinematic_sequence(velocities, fps=10.0)
        
        # 4. 효율 점수
        efficiency = self.calculate_efficiency_score(sequence, velocities)
        
        return {
            'frame_count': len(poses),
            'velocity_estimate': 130 + efficiency['total_score'] * 0.2,  # 추정 (추후 개선)
            'efficiency_score': efficiency['total_score'],
            'overall_grade': efficiency['grade'],
            'peak_times': sequence['peak_times'],
            'violations': sequence['violations'],
            'is_valid_sequence': sequence['is_valid_sequence'],
            'score_breakdown': efficiency['breakdown']
        }
    
    def close(self):
        """리소스 해제"""
        self.pose.close()


# 싱글톤 인스턴스
_engine_instance = None

def get_engine() -> KinematicEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = KinematicEngine()
    return _engine_instance
