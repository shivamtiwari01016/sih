import { createContext, useContext, useState, ReactNode } from 'react'

export type Language = 'en' | 'hi'

interface LanguageContextType {
  lang: Language
  setLang: (lang: Language) => void
  t: (key: string) => string
}

const translations: Record<string, Record<Language, string>> = {
  // Brand & Subtitle
  'brand.name': { en: 'Samanvay (समन्वय)', hi: 'समन्वय (Samanvay)' },
  'brand.subtitle': { en: 'AICTE Secure Complaint Coordination', hi: 'एआईसीटीई सुरक्षित शिकायत समन्वय प्रणाली' },
  'demo.badge': { en: 'OFFICIAL AICTE INTERNAL COMMAND', hi: 'एआईसीटीई आंतरिक कमान एवं नियंत्रण' },

  // Nav
  'nav.my_desk': { en: 'My Desk', hi: 'मेरी कार्य-मेज' },
  'nav.dashboard': { en: 'Overview Dashboard', hi: 'मुख्य डैशबोर्ड' },
  'nav.cop_map': { en: 'Common Operating Picture', hi: 'कॉप भारत मानचित्र' },
  'nav.institutions': { en: 'Institutions', hi: 'संस्थान पंजी' },
  'nav.complaints': { en: 'Complaints Registry', hi: 'शिकायत पंजी' },
  'nav.overlaps': { en: 'Overlap Intelligence', hi: 'ओवरलैप इंटेलिजेंस' },
  'nav.coordination': { en: 'Coordination Rooms', hi: 'समन्वय कक्ष' },
  'nav.accuracy': { en: 'Engine Accuracy', hi: 'इंजन सटीकता' },
  'nav.notifications': { en: 'Alerts & Briefing', hi: 'सूचनाएं एवं ब्रीफिंग' },
  'nav.reports': { en: 'Reports & Analytics', hi: 'रिपोर्ट और विश्लेषण' },
  'nav.bureaus': { en: 'Bureaus', hi: 'ब्यूरो प्रबंधन' },
  'nav.users': { en: 'User Management', hi: 'उपयोगकर्ता प्रबंधन' },
  'nav.audit': { en: 'Audit Trail', hi: 'ऑडिट ट्रेल (हैश-चेन)' },
  'nav.settings': { en: 'Settings', hi: 'सेटिंग्स' },

  // Desk & Status
  'desk.all_clear': { en: 'All Clear! No urgent exceptions pending.', hi: 'सब स्पष्ट है! कोई जरूरी कार्रवाई लंबित नहीं है।' },
  'desk.urgent_queue': { en: 'Prioritized Action Queue', hi: 'प्राथमिकता कार्रवाई कतार' },
  'desk.overlaps_awaiting': { en: 'Overlaps Awaiting My Bureau Reply', hi: 'ओवरलैप जिन पर मेरे ब्यूरो का उत्तर प्रतीक्षित है' },
  'desk.intent_conflicts': { en: 'Action Intent Conflicts', hi: 'कार्रवाई इरादा विरोध (Conflict)' },
  'desk.briefing_btn': { en: 'Daily 60-Second Briefing', hi: 'दैनिक 60-सेकंड ब्रीफिंग' },

  // Buttons & Actions
  'btn.verify_chain': { en: 'Verify Cryptographic Chain', hi: 'क्रिप्टोग्राफिक श्रृंखला सत्यापित करें' },
  'btn.break_glass': { en: 'Break-Glass Emergency Access', hi: 'आपातकालीन ब्रेक-ग्लास पहुंच' },
  'btn.coord_room': { en: 'Open Coordination Room', hi: 'समन्वय कक्ष खोलें' },
  'btn.propose_lead': { en: 'Propose Lead Bureau', hi: 'नेतृत्व ब्यूरो का प्रस्ताव दें' },
  'btn.accept_lead': { en: 'Accept Lead Bureau', hi: 'नेतृत्व स्वीकार करें' },
  'btn.quick_call': { en: 'Request a Quick Call', hi: 'शीघ्र कॉल का अनुरोध करें' },
  'btn.joint_decision': { en: 'Record Joint Decision', hi: 'संयुक्त निर्णय दर्ज करें' },
  'btn.register_intent': { en: 'Register Action Intent', hi: 'कार्रवाई इरादा पंजीकृत करें' },
  'btn.nl_search': { en: 'Natural Language Search', hi: 'प्राकृतिक भाषा खोज' },

  // Overlap Banner
  'banner.pre_check_title': { en: 'Potential Overlapping Case Detected', hi: 'संभावित ओवरलैप मामला पहचाना गया' },
  'banner.save_and_open': { en: 'Save & Open Coordination Room', hi: 'सहेजें और समन्वय कक्ष खोलें' },

  // General
  'status.received': { en: 'Received', hi: 'प्राप्त' },
  'status.under_process': { en: 'Under Process', hi: 'प्रक्रियाधीन' },
  'status.disposed': { en: 'Disposed', hi: 'निस्तारित' },
  'status.escalated': { en: 'Escalated', hi: 'उच्चाधिकारी को प्रेषित' },

  // Institution EDA Detail
  'inst.detail': { en: 'Institution Detail & EDA', hi: 'संस्थान विवरण एवं डेटा विश्लेषण' },
  'inst.overview_eda': { en: 'Overview & EDA', hi: 'अवलोकन एवं विश्लेषण' },
  'inst.cases': { en: 'Cases', hi: 'शिकायतें' },
  'inst.overlaps': { en: 'Overlaps', hi: 'ओवरलैप' },
  'inst.timeline': { en: 'Timeline', hi: 'टाइमलाइन' },
  'inst.watch': { en: 'Watch', hi: 'निगरानी' },
  'inst.watching': { en: 'Watching', hi: 'निगरानी में' },
  'inst.add_complaint': { en: 'Add Complaint', hi: 'शिकायत दर्ज करें' },
  'inst.risk_score': { en: 'Risk Score', hi: 'जोखिम स्कोर' },
  'inst.insufficient_data': { en: 'Not enough data for trends (< 5 complaints on record)', hi: 'रुझानों के लिए पर्याप्त डेटा नहीं (< 5 शिकायतें)' },
}

const LanguageContext = createContext<LanguageContextType>({
  lang: 'en',
  setLang: () => {},
  t: (key: string) => key,
})

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    const saved = localStorage.getItem('samanvay_lang') as Language
    return saved === 'hi' ? 'hi' : 'en'
  })

  const setLang = (newLang: Language) => {
    setLangState(newLang)
    localStorage.setItem('samanvay_lang', newLang)
  }

  const t = (key: string): string => {
    return translations[key]?.[lang] || translations[key]?.en || key
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  return useContext(LanguageContext)
}
