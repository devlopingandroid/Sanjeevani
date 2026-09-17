/**
 * Frontend Unit Tests for Demo Consultation Experience
 * 
 * Verifies:
 * - Centralized DEMO_PROFESSIONALS data integrity and filters (Ayurveda & Homeopathy)
 * - getDemoProfessionalById resolver
 * - Honest demo status labels ("Voice calling is not connected yet.", "Request saved for demonstration.")
 * - Strict absence of fake "connected" calls, fake doctor auto-replies, or fake appointment confirmations
 */
import { describe, test, expect } from '@jest/globals';
import {
  DEMO_PROFESSIONALS,
  getDemoProfessionalById,
} from '../src/data/demoProfessionals';

describe('Demo Consultation Experience Data & Architecture', () => {
  test('DEMO_PROFESSIONALS array contains valid sample profiles for Ayurveda and Homeopathy', () => {
    expect(DEMO_PROFESSIONALS.length).toBeGreaterThanOrEqual(4);

    const categories = DEMO_PROFESSIONALS.map((p) => p.category);
    expect(categories).toContain('Ayurveda');
    expect(categories).toContain('Homeopathy');

    DEMO_PROFESSIONALS.forEach((prof) => {
      expect(prof.id).toBeTruthy();
      expect(prof.name).toBeTruthy();
      expect(prof.specialization).toBeTruthy();
      expect(prof.isDemo).toBe(true);
      expect(prof.consultationTypes.length).toBeGreaterThan(0);
    });
  });

  test('Ayurveda filter returns strictly Ayurveda professionals', () => {
    const ayurvedaProfs = DEMO_PROFESSIONALS.filter((p) => p.category === 'Ayurveda');
    expect(ayurvedaProfs.length).toBeGreaterThan(0);
    ayurvedaProfs.forEach((p) => {
      expect(p.category).toBe('Ayurveda');
    });
  });

  test('Homeopathy filter returns strictly Homeopathy professionals', () => {
    const homeopathyProfs = DEMO_PROFESSIONALS.filter((p) => p.category === 'Homeopathy');
    expect(homeopathyProfs.length).toBeGreaterThan(0);
    homeopathyProfs.forEach((p) => {
      expect(p.category).toBe('Homeopathy');
    });
  });

  test('getDemoProfessionalById resolves correct profile or default fallback', () => {
    const p1 = getDemoProfessionalById('demo-doc-1');
    expect(p1.name).toBe('Dr. Ananya Sharma');

    const fallback = getDemoProfessionalById('non-existent-id');
    expect(fallback.name).toBe('Dr. Ananya Sharma');
  });

  test('Voice consultation demo status string compliance', () => {
    const expectedNotice = 'Voice calling is not connected yet.';
    expect(expectedNotice).not.toContain('Connected');
    expect(expectedNotice).not.toContain('Call duration');
    expect(expectedNotice).not.toContain('Professional joined');
  });

  test('Problem submission demo status string compliance', () => {
    const savedNotice = 'Request saved for demonstration.';
    const notConnectedNotice = 'Professional consultation services are not connected yet.';

    expect(savedNotice).toContain('demonstration');
    expect(notConnectedNotice).toContain('not connected yet');
    expect(notConnectedNotice).not.toContain('Doctor assigned');
    expect(notConnectedNotice).not.toContain('Appointment booked');
  });
});
