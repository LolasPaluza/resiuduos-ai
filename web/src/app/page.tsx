import { HeroSection } from "@/components/landing/hero";
import { LandingNavbar } from "@/components/landing/navbar";
import {
  ComoFuncionaSection,
  ContatoSection,
  EticaSection,
  FinanceiroSection,
  HardwareSection,
  IndustriaSection,
  LandingFooter,
  MateriaisSection,
  ProblemaSection,
} from "@/components/landing/sections";

export default function HomePage() {
  return (
    <>
      <LandingNavbar />
      <main className="relative">
        <HeroSection />
        <ProblemaSection />
        <ComoFuncionaSection />
        <MateriaisSection />
        <FinanceiroSection />
        <IndustriaSection />
        <EticaSection />
        <HardwareSection />
        <ContatoSection />
      </main>
      <LandingFooter />
    </>
  );
}
