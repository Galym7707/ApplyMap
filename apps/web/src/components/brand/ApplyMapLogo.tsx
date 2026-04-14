import Image from "next/image";
import { cn } from "@/lib/utils";

type ApplyMapLogoProps = {
  className?: string;
};

export function ApplyMapLogo({ className }: ApplyMapLogoProps) {
  return (
    <Image
      src="/applymap-logo.png"
      alt="ApplyMap"
      width={1004}
      height={315}
      className={cn("h-8 w-auto object-contain", className)}
    />
  );
}
