
import mermaid from 'mermaid';
import logos from '@iconify-json/logos/icons.json';


mermaid.initialize({ startOnLoad: true });
mermaid.registerIconPacks([
    {
        name: 'logos',
        loader: () => Promise.resolve(logos),
    },
]);