/**
 * Centralized Demo Data Source for Professional Support
 * 
 * Provides sample profiles for UI demonstration ONLY.
 * Easily replaceable with real GET /api/v1/professionals backend API later.
 */

export interface DemoProfessional {
  id: string;
  name: string;
  specialization: string;
  category: 'Ayurveda' | 'Homeopathy';
  consultationTypes: ('chat' | 'voice')[];
  bio: string;
  isDemo: boolean;
}

export const DEMO_PROFESSIONALS: DemoProfessional[] = [
  {
    id: 'demo-doc-1',
    name: 'Dr. Ananya Sharma',
    specialization: 'Ayurveda & General Wellness',
    category: 'Ayurveda',
    consultationTypes: ['chat', 'voice'],
    bio: 'Specializing in holistic Ayurvedic practices, lifestyle balance, and stress relief through natural restorative therapies.',
    isDemo: true,
  },
  {
    id: 'demo-doc-2',
    name: 'Dr. Rahul Verma',
    specialization: 'Homeopathy & General Wellness',
    category: 'Homeopathy',
    consultationTypes: ['chat', 'voice'],
    bio: 'Focusing on individualized homeopathic care for constitutional wellness, emotional balance, and mind-body harmony.',
    isDemo: true,
  },
  {
    id: 'demo-doc-3',
    name: 'Dr. Meera Kapoor',
    specialization: 'Ayurveda, Lifestyle & Wellness',
    category: 'Ayurveda',
    consultationTypes: ['chat', 'voice'],
    bio: 'Dedicated to restorative Ayurvedic routines, dietary guidance, and somatic stress mitigation.',
    isDemo: true,
  },
  {
    id: 'demo-doc-4',
    name: 'Dr. Arjun Mehta',
    specialization: 'Homeopathy & Wellness',
    category: 'Homeopathy',
    consultationTypes: ['chat', 'voice'],
    bio: 'Specialized in gentle homeopathic remedies for emotional wellbeing, stress resistance, and vitality.',
    isDemo: true,
  },
];

export function getDemoProfessionalById(id?: string): DemoProfessional {
  if (!id) return DEMO_PROFESSIONALS[0];
  return DEMO_PROFESSIONALS.find((p) => p.id === id) || DEMO_PROFESSIONALS[0];
}
