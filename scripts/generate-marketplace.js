const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');

const root = path.resolve(__dirname, '..');
const checkOnly = process.argv.includes('--check');

function requireText(value, label) {
    if (typeof value !== 'string' || !value.trim()) {
        throw new Error(`${label} 必须是非空字符串`);
    }
    return value;
}

function requireStringArray(value, label) {
    if (!Array.isArray(value)) throw new Error(`${label} 必须是字符串数组`);
    value.forEach((item, index) => requireText(item, `${label}[${index}]`));
    return value;
}

function readMetadata(relativePath, fields) {
    const data = JSON.parse(fs.readFileSync(path.join(root, relativePath), 'utf8'));
    for (const field of fields) requireText(data[field], `${relativePath}: ${field}`);
    return data;
}

function directories(relativePath) {
    return fs.readdirSync(path.join(root, relativePath), { withFileTypes: true })
        .filter(entry => entry.isDirectory())
        .map(entry => entry.name)
        .sort();
}

function buildConfigs() {
    const metadata = readMetadata('marketplace.metadata.json', [
        'name', 'displayName', 'description', 'repository'
    ]);
    requireText(metadata.owner?.name, 'marketplace.metadata.json: owner.name');
    const workbuddyMarketplace = {
        name: metadata.name,
        description: `${metadata.displayName}：${metadata.description}`,
        owner: metadata.owner,
        plugins: []
    };
    const codexMarketplace = {
        name: metadata.name,
        interface: { displayName: metadata.displayName },
        plugins: []
    };
    const outputs = new Map();

    for (const pluginName of directories('plugins')) {
        const pluginRoot = `plugins/${pluginName}`;
        const skillsRoot = `${pluginRoot}/skills`;
        if (!fs.existsSync(path.join(root, skillsRoot))) continue;
        const skillPaths = directories(skillsRoot).map(skillName => {
            const skillFile = `${skillsRoot}/${skillName}/SKILL.md`;
            const { data } = matter(fs.readFileSync(path.join(root, skillFile), 'utf8'));
            requireText(data.name, `${skillFile}: name`);
            requireText(data.description, `${skillFile}: description`);
            if (data.name !== skillName) throw new Error(`${skillFile}: name 必须与技能目录名一致`);
            return `./skills/${skillName}`;
        });
        if (!skillPaths.length) continue;

        const metadataFile = `${pluginRoot}/metadata.json`;
        const plugin = readMetadata(metadataFile, [
            'version', 'displayName', 'shortDescription', 'longDescription', 'category'
        ]);
        if (!/^\d+\.\d+\.\d+(?:-[\w.-]+)?(?:\+[\w.-]+)?$/.test(plugin.version)) {
            throw new Error(`${metadataFile}: version 必须为语义版本号`);
        }
        requireStringArray(plugin.keywords, `${metadataFile}: keywords`);
        requireStringArray(plugin.defaultPrompt, `${metadataFile}: defaultPrompt`);
        if (plugin.defaultPrompt.length > 3 || plugin.defaultPrompt.some(prompt => [...prompt].length > 128)) {
            throw new Error(`${metadataFile}: defaultPrompt 最多 3 条，每条最多 128 个字符`);
        }

        const homepage = `${metadata.repository}/tree/main/${pluginRoot}`;
        const common = {
            name: pluginName,
            version: plugin.version,
            description: plugin.shortDescription,
            author: metadata.owner,
            homepage,
            repository: metadata.repository,
            keywords: plugin.keywords
        };
        // WorkBuddy 使用英文 name 作为标识；中文套件名放在简介中。
        outputs.set(`${pluginRoot}/.codebuddy-plugin/plugin.json`, {
            ...common,
            description: `${plugin.displayName}：${plugin.shortDescription}`,
            category: plugin.category,
            skills: skillPaths
        });
        outputs.set(`${pluginRoot}/.codex-plugin/plugin.json`, {
            ...common,
            skills: './skills/',
            interface: {
                displayName: plugin.displayName,
                shortDescription: plugin.shortDescription,
                longDescription: plugin.longDescription,
                developerName: metadata.owner.name,
                category: plugin.category,
                capabilities: ['Read', 'Write'],
                websiteURL: homepage,
                defaultPrompt: plugin.defaultPrompt
            }
        });
        workbuddyMarketplace.plugins.push({
            name: pluginName,
            source: `./${pluginRoot}`,
            description: `${plugin.displayName}：${plugin.shortDescription}`,
            version: plugin.version,
            author: metadata.owner,
            homepage,
            repository: metadata.repository,
            keywords: plugin.keywords,
            category: plugin.category,
            strict: true
        });
        codexMarketplace.plugins.push({
            name: pluginName,
            source: { source: 'local', path: `./${pluginRoot}` },
            policy: { installation: 'AVAILABLE', authentication: 'ON_INSTALL' },
            category: plugin.category
        });
    }
    outputs.set('.codebuddy-plugin/marketplace.json', workbuddyMarketplace);
    outputs.set('.agents/plugins/marketplace.json', codexMarketplace);
    return outputs;
}

try {
    // 所有输入通过校验后才写入，避免因文案或技能元数据错误生成部分配置。
    const outputs = buildConfigs();
    const staleFiles = [];
    for (const [relativePath, config] of outputs) {
        const file = path.join(root, relativePath);
        const contents = `${JSON.stringify(config, null, 2)}\n`;
        if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === contents) continue;
        if (checkOnly) {
            staleFiles.push(relativePath);
        } else {
            fs.mkdirSync(path.dirname(file), { recursive: true });
            fs.writeFileSync(file, contents);
        }
    }
    if (staleFiles.length) {
        throw new Error(`以下配置需要运行 npm run generate 同步：\n${staleFiles.join('\n')}`);
    }
    console.log(checkOnly ? '配置校验通过，生成结果与源配置一致。' : 'WorkBuddy 和 Codex 配置已生成。');
} catch (error) {
    console.error(`配置${checkOnly ? '校验' : '生成'}失败：${error.message}`);
    process.exitCode = 1;
}
