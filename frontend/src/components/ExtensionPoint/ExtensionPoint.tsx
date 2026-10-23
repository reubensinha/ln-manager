import { Suspense } from "react";
import { Skeleton } from "@mantine/core";

import { usePluginExtensions } from "../../extensions/usePluginExtensions";
import ExtensionErrorBoundary from "./ExtensionErrorBoundary";

interface ExtensionPointProps<TContext> {
  /** An id from `extensions/extensionPoints.ts`. */
  id: string;
  /** Handed to every contributed component; memoise it at the call site. */
  context: TContext;
}

/**
 * Renders every component plugins have registered for this point.
 *
 * Each contribution gets its own error boundary and Suspense boundary so one plugin
 * can neither crash the page nor block the others' lazy chunks.
 */
function ExtensionPoint<TContext>({ id, context }: ExtensionPointProps<TContext>) {
  const extensions = usePluginExtensions<TContext>(id);

  if (extensions.length === 0) return null;

  return (
    <>
      {extensions.map(({ pluginName, extension }) => {
        const Component = extension.component;
        return (
          <ExtensionErrorBoundary
            key={`${pluginName}:${extension.id}`}
            pluginName={pluginName}
            resetKey={context}
          >
            <Suspense fallback={<Skeleton height={120} my="md" />}>
              <Component context={context} />
            </Suspense>
          </ExtensionErrorBoundary>
        );
      })}
    </>
  );
}

export default ExtensionPoint;
